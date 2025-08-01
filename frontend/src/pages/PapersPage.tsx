import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FileText, Loader2, AlertCircle, Eye, RotateCcw, Clock, Trash2 } from 'lucide-react';
import { 
  listPapers, 
  createProgressWebSocket, 
  handleApiError,
  retryPaper,
  deletePaper
} from '@/services/api';
import { 
  PaperMetadata, 
  ProcessingProgress
} from '@/types';
import { useNotification } from '@/context/NotificationContext';

export const PapersPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showNotification } = useNotification();
  const [isLoading, setIsLoading] = useState(true);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [papers, setPapers] = useState<PaperMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeWebSocket, setActiveWebSocket] = useState<WebSocket | null>(null);

  // Load existing papers on component mount
  useEffect(() => {
    loadPapers();
  }, []);

  // Handle navigation from process page with new paper
  useEffect(() => {
    const state = location.state as { newPaperId?: string; showProcessing?: boolean };
    if (state?.newPaperId && state?.showProcessing) {
      // Show success notification
      showNotification('Paper submitted successfully! Processing has started.', 'success');
      
      // Start tracking the new paper's progress
      startProgressTracking(state.newPaperId);
      
      // Clear the state to prevent re-triggering
      window.history.replaceState({}, document.title);
    }
  }, [location.state, showNotification]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (activeWebSocket) {
        activeWebSocket.close();
      }
    };
  }, [activeWebSocket]);

  const loadPapers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await listPapers(1, 50); // Load up to 50 recent papers
      setPapers(response.papers);
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to load papers: ${errorMessage}`);
      console.error('Error loading papers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const startProgressTracking = (paperId: string) => {
    // Close any existing WebSocket
    if (activeWebSocket) {
      activeWebSocket.close();
    }

    // Set up WebSocket for progress tracking
    const ws = createProgressWebSocket(
      paperId,
      (progress: ProcessingProgress) => {
        setProcessingProgress(progress);
        
        // Reload papers to show updated status
        loadPapers();
        
        // If processing completed or failed, clean up
        if (progress.status === 'completed' || progress.status === 'failed') {
          if (progress.status === 'completed') {
            showNotification('Paper processing completed successfully!', 'success');
          } else if (progress.status === 'failed') {
            setError(progress.error || 'Processing failed');
            showNotification('Paper processing failed. Please check the error details.', 'error');
          }
          setProcessingProgress(null);
          if (activeWebSocket) {
            activeWebSocket.close();
            setActiveWebSocket(null);
          }
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error during processing');
      },
      () => {
        console.log('WebSocket connection closed');
        setActiveWebSocket(null);
      }
    );
    
    setActiveWebSocket(ws);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'badge badge-success';
      case 'failed':
        return 'badge badge-error';
      case 'pending':
      case 'fetching':
      case 'fetching_arxiv':
      case 'fetching_content':
      case 'processing_images':
      case 'extracting':
      case 'extracting_structure':
      case 'extracting_content':
      case 'generating':
      case 'generating_html':
      case 'generating_pdf':
      case 'finalizing':
        return 'badge badge-warning';
      default:
        return 'badge badge-neutral';
    }
  };

  const getStatusDisplayName = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Queued';
      case 'fetching':
        return 'Fetching';
      case 'fetching_arxiv':
        return 'Fetching ArXiv';
      case 'fetching_content':
        return 'Processing Content';
      case 'processing_images':
        return 'Processing Images';
      case 'extracting':
        return 'Extracting';
      case 'extracting_structure':
        return 'Analyzing Structure';
      case 'extracting_content':
        return 'AI Extraction';
      case 'generating':
        return 'Generating';
      case 'generating_html':
        return 'Creating HTML';
      case 'generating_pdf':
        return 'Creating PDF';
      case 'finalizing':
        return 'Finalizing';
      default:
        return status;
    }
  };

  const handleViewPaper = (paperId: string) => {
    navigate(`/papers/${paperId}`);
  };

  const handleRetryPaper = async (paperId: string) => {
    try {
      setError(null);
      await retryPaper(paperId);
      
      // Reload papers to show updated status
      loadPapers();
      
      // Set up WebSocket for retry progress tracking
      const ws = createProgressWebSocket(
        paperId,
        (progress: ProcessingProgress) => {
          setProcessingProgress(progress);
          loadPapers();
          
          if (progress.status === 'completed' || progress.status === 'failed') {
            if (progress.status === 'failed') {
              setError(progress.error || 'Retry failed');
            }
            setProcessingProgress(null);
            if (activeWebSocket) {
              activeWebSocket.close();
              setActiveWebSocket(null);
            }
          }
        },
        (error) => {
          console.error('WebSocket error during retry:', error);
          setError('Connection error during retry');
        }
      );
      
      setActiveWebSocket(ws);
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Retry failed: ${errorMessage}`);
      console.error('Error retrying paper:', err);
    }
  };

  const handleDeletePaper = async (paperId: string, paperTitle: string) => {
    // Show confirmation dialog
    const confirmDelete = window.confirm(
      `Are you sure you want to delete "${paperTitle}"?\n\n` +
      'This will permanently remove:\n' +
      '• The paper record from the database\n' +
      '• All generated files (HTML, PDF, images)\n' +
      '• All associated metadata\n\n' +
      'This action cannot be undone.'
    );

    if (!confirmDelete) {
      return;
    }

    try {
      setError(null);
      await deletePaper(paperId);
      
      // Show success notification
      showNotification(`Paper "${paperTitle}" has been deleted successfully.`, 'success');
      
      // Reload papers to reflect the deletion
      loadPapers();
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to delete paper: ${errorMessage}`);
      showNotification(`Failed to delete paper: ${errorMessage}`, 'error');
      console.error('Error deleting paper:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Papers</h1>
        <button 
          className="btn-primary btn-md"
          onClick={() => navigate('/process')}
        >
          Process New Paper
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="card-content py-2">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <p>{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Processing Progress */}
      {processingProgress && (
        <div className="card">
          <div className="card-content py-2">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">Processing Paper</h3>
                <span className={getStatusBadgeClass(processingProgress.status)}>
                  {processingProgress.status}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>{processingProgress.message}</span>
                  <span>{Math.round(processingProgress.progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${processingProgress.progress}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}


      {/* Papers List */}
      <div>
        {isLoading ? (
          <div className="card">
            <div className="card-content py-2">
              <div className="flex items-center justify-center space-x-2 text-gray-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                <p>Loading papers...</p>
              </div>
            </div>
          </div>
        ) : papers.length > 0 ? (
          papers.map((paper) => (
            <div key={paper.paper_id} className="card hover:shadow-md transition-shadow duration-200">
              <div className="card-content py-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <FileText className="w-5 h-5 text-gray-400 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">
                        {paper.title}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}
                      </p>
                      {paper.arxiv_url && (
                        <p className="text-sm">
                          <a 
                            href={paper.arxiv_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                            onClick={(e) => e.stopPropagation()}
                            title="View original paper on ArXiv"
                          >
                            {paper.arxiv_url}
                          </a>
                        </p>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>
                          Processed {new Date(paper.created_at).toLocaleDateString()}
                        </span>
                        <span>
                          {paper.processing_time}s
                        </span>
                        <span>
                          {paper.output_format} • {paper.language}
                        </span>
                        {paper.retry_count > 0 && (
                          <span className="flex items-center text-orange-600">
                            <RotateCcw className="w-3 h-3 mr-1" />
                            Retried {paper.retry_count}x
                          </span>
                        )}
                      </div>

                      {/* Error message for failed papers */}
                      {paper.status === 'failed' && paper.error_message && (
                        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="flex items-start space-x-2">
                            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm text-red-800 font-medium">Processing failed:</p>
                              <p className="text-sm text-red-700 mt-1">{paper.error_message}</p>
                              {paper.last_failed_at && (
                                <div className="flex items-center space-x-1 mt-2 text-xs text-red-600">
                                  <Clock className="w-3 h-3" />
                                  <span>
                                    Failed on {new Date(paper.last_failed_at).toLocaleString()}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {paper.status === 'completed' && (
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewPaper(paper.paper_id);
                        }}
                        title="View Output"
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View
                      </button>
                    )}
                    {paper.status === 'failed' && (
                      <button
                        className="btn btn-outline btn-sm text-blue-600 hover:text-blue-700 hover:border-blue-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRetryPaper(paper.paper_id);
                        }}
                        title="Retry processing this paper"
                      >
                        <RotateCcw className="w-4 h-4 mr-1" />
                        Retry
                      </button>
                    )}
                    <button
                      className="btn btn-outline btn-sm text-red-600 hover:text-red-700 hover:border-red-300"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePaper(paper.paper_id, paper.title);
                      }}
                      title="Delete this paper permanently"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </button>
                    <span className={getStatusBadgeClass(paper.status)}>
                      {getStatusDisplayName(paper.status)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="card">
            <div className="card-content py-2">
              <div className="text-center space-y-4">
                <p className="text-gray-600">
                  Your processed papers will appear here. Start by processing your first paper!
                </p>
                <button 
                  className="btn-primary btn-md"
                  onClick={() => navigate('/process')}
                >
                  Process Your First Paper
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
