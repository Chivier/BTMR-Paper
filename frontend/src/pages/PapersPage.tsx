import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, Loader2, AlertCircle, Eye, RotateCcw, Clock, Trash2, Search, X } from 'lucide-react';
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
  const { t } = useTranslation('pages');
  const navigate = useNavigate();
  const location = useLocation();
  const { showNotification } = useNotification();
  const [isLoading, setIsLoading] = useState(true);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [papers, setPapers] = useState<PaperMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeWebSocket, setActiveWebSocket] = useState<WebSocket | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Filtered papers based on search query
  const filteredPapers = useMemo(() => {
    if (!searchQuery.trim()) {
      return papers;
    }
    
    const query = searchQuery.toLowerCase();
    
    return papers.filter((paper) => {
      // Search by title
      if (paper.title.toLowerCase().includes(query)) {
        return true;
      }
      
      // Search by authors
      const authorsText = Array.isArray(paper.authors) 
        ? paper.authors.join(' ').toLowerCase()
        : paper.authors.toLowerCase();
      if (authorsText.includes(query)) {
        return true;
      }
      
      // Search by arXiv ID/URL
      if (paper.arxiv_url && paper.arxiv_url.toLowerCase().includes(query)) {
        return true;
      }
      
      // Extract arXiv ID from URL for more targeted searching
      // ArXiv URLs typically follow patterns like:
      // https://arxiv.org/abs/2301.12345
      // https://arxiv.org/pdf/2301.12345.pdf
      if (paper.arxiv_url) {
        const arxivIdMatch = paper.arxiv_url.match(/(?:abs\/|pdf\/)(\d{4}\.\d{4,5})/);
        if (arxivIdMatch && arxivIdMatch[1].includes(query)) {
          return true;
        }
      }
      
      return false;
    });
  }, [papers, searchQuery]);

  // Load existing papers on component mount
  useEffect(() => {
    loadPapers();
  }, []);

  // Handle navigation from process page with new paper
  useEffect(() => {
    const state = location.state as { newPaperId?: string; showProcessing?: boolean };
    if (state?.newPaperId && state?.showProcessing) {
      // Show success notification
      showNotification(t('papers.notifications.submitted'), 'success');
      
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
      setError(t('papers.errors.loadFailed', { error: errorMessage }));
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
            showNotification(t('papers.notifications.completed'), 'success');
          } else if (progress.status === 'failed') {
            setError(progress.error || t('papers.errors.processingFailed'));
            showNotification(t('papers.notifications.failed'), 'error');
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
        setError(t('papers.notifications.connectionError'));
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
    return t(`papers.status.${status}`, { defaultValue: status });
  };

  const getLanguageDisplayName = (languageCode: string) => {
    return t(`languages.${languageCode}`, { defaultValue: languageCode });
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
              setError(progress.error || t('papers.errors.processingFailed'));
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
          setError(t('papers.notifications.connectionErrorRetry'));
        }
      );
      
      setActiveWebSocket(ws);
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(t('papers.notifications.retryFailed', { error: errorMessage }));
      console.error('Error retrying paper:', err);
    }
  };

  const handleDeletePaper = async (paperId: string, paperTitle: string) => {
    // Show confirmation dialog
    const confirmDelete = window.confirm(
      t('papers.deleteConfirm.message', { title: paperTitle }) + '\n\n' +
      t('papers.deleteConfirm.warning') + '\n' +
      t('papers.deleteConfirm.items.database') + '\n' +
      t('papers.deleteConfirm.items.files') + '\n' +
      t('papers.deleteConfirm.items.metadata') + '\n\n' +
      t('papers.deleteConfirm.undoWarning')
    );

    if (!confirmDelete) {
      return;
    }

    try {
      setError(null);
      await deletePaper(paperId);
      
      // Show success notification
      showNotification(t('papers.notifications.deleteSuccess', { title: paperTitle }), 'success');
      
      // Reload papers to reflect the deletion
      loadPapers();
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(t('papers.errors.deleteFailed', { error: errorMessage }));
      showNotification(t('papers.notifications.deleteFailed', { error: errorMessage }), 'error');
      console.error('Error deleting paper:', err);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col space-y-4 sm:flex-row sm:justify-between sm:items-center sm:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">{t('papers.title')}</h1>
        <button 
          className="btn-primary btn-md"
          onClick={() => navigate('/process')}
        >
          {t('papers.processNewPaper')}
        </button>
      </div>

      {/* Search Section */}
      <div className="card">
        <div className="card-content py-2">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label htmlFor="search" className="sr-only">
                {t('papers.search.label')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="search"
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input input-bordered w-full pl-10 pr-10"
                  placeholder={t('papers.search.placeholder')}
                />
                {searchQuery && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                    <button
                      type="button"
                      onClick={handleClearSearch}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                      title={t('papers.search.clearSearch')}
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
            {searchQuery && (
              <div className="text-sm text-gray-600">
                {t('papers.search.resultCount', { count: filteredPapers.length })}
              </div>
            )}
          </div>
        </div>
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
                <h3 className="font-medium text-gray-900">{t('papers.processingPaper')}</h3>
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
                <p>{t('papers.loading')}</p>
              </div>
            </div>
          </div>
        ) : papers.length > 0 ? (
          filteredPapers.length > 0 ? (
            filteredPapers.map((paper) => (
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
                          {new Date(paper.created_at).toLocaleDateString()}
                        </span>
                        <span>
                          {paper.processing_time}s
                        </span>
                        <span>
                          {getLanguageDisplayName(paper.language)}
                        </span>
                        {paper.retry_count > 0 && (
                          <span className="flex items-center text-orange-600">
                            <RotateCcw className="w-3 h-3 mr-1" />
                            {t('papers.retried', { count: paper.retry_count })}
                          </span>
                        )}
                      </div>

                      {/* Error message for failed papers */}
                      {paper.status === 'failed' && paper.error_message && (
                        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="flex items-start space-x-2">
                            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm text-red-800 font-medium">{t('papers.processingFailed')}:</p>
                              <p className="text-sm text-red-700 mt-1">{paper.error_message}</p>
                              {paper.last_failed_at && (
                                <div className="flex items-center space-x-1 mt-2 text-xs text-red-600">
                                  <Clock className="w-3 h-3" />
                                  <span>
                                    {t('papers.failedOn')} {new Date(paper.last_failed_at).toLocaleString()}
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
                        {t('papers.actions.view')}
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
                        {t('papers.actions.retry')}
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
                      {t('papers.actions.delete')}
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
            // No search results
            <div className="card">
              <div className="card-content py-2">
                <div className="text-center space-y-4">
                  <p className="text-gray-600">
                    {t('papers.search.noResults')}
                  </p>
                  <button 
                    className="btn btn-outline btn-sm"
                    onClick={handleClearSearch}
                  >
                    {t('papers.search.clearSearch')}
                  </button>
                </div>
              </div>
            </div>
          )
        ) : (
          <div className="card">
            <div className="card-content py-2">
              <div className="text-center space-y-4">
                <p className="text-gray-600">
                  {t('papers.emptyState')}
                </p>
                <button 
                  className="btn-primary btn-md"
                  onClick={() => navigate('/process')}
                >
                  {t('papers.processFirstPaper')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
