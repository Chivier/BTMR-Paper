import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Link, FileText, Loader2, AlertCircle, Eye } from 'lucide-react';
import { 
  processPaper, 
  uploadFile, 
  listPapers, 
  createProgressWebSocket, 
  handleApiError,
  isValidArxivUrl,
  isValidUrl
} from '@/services/api';
import { 
  PaperProcessRequest, 
  PaperMetadata, 
  ProcessingProgress, 
  UploadedFile 
} from '@/types';

export const PapersPage: React.FC = () => {
  const navigate = useNavigate();
  const [showProcessForm, setShowProcessForm] = useState(false);
  const [inputType, setInputType] = useState<'url' | 'file'>('url');
  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [papers, setPapers] = useState<PaperMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeWebSocket, setActiveWebSocket] = useState<WebSocket | null>(null);

  // Load existing papers on component mount
  useEffect(() => {
    loadPapers();
  }, []);

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

  const handleProcessPaper = async () => {
    if (!inputValue.trim() && !selectedFile) return;
    
    setIsProcessing(true);
    setError(null);
    setProcessingProgress(null);
    
    try {
      let uploadedFileData = null;
      
      // Step 1: Handle file upload if needed
      if (inputType === 'file' && selectedFile) {
        uploadedFileData = await uploadFile(selectedFile, (progress) => {
          setUploadProgress(progress);
        });
        setUploadProgress(100);
      }
      
      // Step 2: Determine input type and source
      let input_type: PaperProcessRequest['input_type'];
      let input_source: string;
      
      if (inputType === 'file' && uploadedFileData) {
        input_type = 'pdf';
        input_source = uploadedFileData.file_path;
      } else {
        // URL processing
        input_source = inputValue;
        if (isValidArxivUrl(inputValue)) {
          input_type = 'arxiv';
        } else if (isValidUrl(inputValue)) {
          input_type = 'url';
        } else {
          throw new Error('Invalid URL format. Please provide a valid ArXiv URL or direct paper URL.');
        }
      }
      
      // Step 3: Create processing request
      const request: PaperProcessRequest = {
        input_source,
        input_type,
        output_format: 'html',
        language: 'en',
        save_json: true
      };
      
      // Step 4: Start paper processing
      const response = await processPaper(request);
      const paperId = response.paper_id;
      
      // Reset form immediately
      setShowProcessForm(false);
      setInputValue('');
      setSelectedFile(null);
      setUploadProgress(0);
      
      // Reload papers list to show the new pending paper from backend
      loadPapers();
      
      // Step 5: Set up WebSocket for progress tracking
      const ws = createProgressWebSocket(
        paperId,
        (progress: ProcessingProgress) => {
          setProcessingProgress(progress);
          
          // Reload papers to get updated status
          loadPapers();
          
          // If processing completed or failed, clear progress and clean up
          if (progress.status === 'completed' || progress.status === 'failed') {
            if (progress.status === 'failed') {
              setError(progress.error || 'Processing failed');
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
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      console.error('Error processing paper:', err);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setInputValue(file.name);
      setUploadProgress(0);
    }
  };
  
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'badge badge-success';
      case 'failed':
        return 'badge badge-error';
      case 'pending':
      case 'fetching':
      case 'extracting':
      case 'generating':
        return 'badge badge-warning';
      default:
        return 'badge badge-neutral';
    }
  };

  const handleViewPaper = (paperId: string) => {
    navigate(`/papers/${paperId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Papers</h1>
        <button 
          className="btn-primary btn-md"
          onClick={() => setShowProcessForm(!showProcessForm)}
        >
          Process New Paper
        </button>
      </div>

      {showProcessForm && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Process New Paper</h3>
            <p className="card-description">
              Upload a PDF file or provide a URL to an academic paper
            </p>
          </div>
          <div className="card-content space-y-4">
            {/* Input Type Selection */}
            <div className="flex space-x-4">
              <button
                className={`btn ${inputType === 'url' ? 'btn-primary' : 'btn-outline'} btn-sm`}
                onClick={() => setInputType('url')}
              >
                <Link className="w-4 h-4 mr-2" />
                URL
              </button>
              <button
                className={`btn ${inputType === 'file' ? 'btn-primary' : 'btn-outline'} btn-sm`}
                onClick={() => setInputType('file')}
              >
                <Upload className="w-4 h-4 mr-2" />
                File Upload
              </button>
            </div>

            {/* Input Field */}
            {inputType === 'url' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Paper URL (ArXiv, DOI, or direct link)
                </label>
                <input
                  type="url"
                  className="input"
                  placeholder="https://arxiv.org/abs/2301.12345"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload PDF File
                </label>
                <div className="dropzone">
                  <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600">
                    Click to upload or drag and drop your PDF file here
                  </p>
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                className="btn-primary btn-md"
                onClick={handleProcessPaper}
                disabled={!inputValue.trim() || isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Process Paper'
                )}
              </button>
              <button
                className="btn-outline btn-md"
                onClick={() => setShowProcessForm(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="card-content">
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
          <div className="card-content py-5">
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

      {/* Upload Progress */}
      {inputType === 'file' && uploadProgress > 0 && uploadProgress < 100 && (
        <div className="card">
          <div className="card-content">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading file...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Papers List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="card">
            <div className="card-content">
              <div className="flex items-center justify-center space-x-2 text-gray-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                <p>Loading papers...</p>
              </div>
            </div>
          </div>
        ) : papers.length > 0 ? (
          papers.map((paper) => (
            <div key={paper.paper_id} className="card hover:shadow-md transition-shadow duration-200">
              <div className="card-content py-5">
                <div className="flex items-start justify-between">
                  <div 
                    className="flex items-start space-x-3 flex-1 cursor-pointer"
                    onClick={() => handleViewPaper(paper.paper_id)}
                  >
                    <FileText className="w-5 h-5 text-gray-400 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 hover:text-blue-600 transition-colors">
                        {paper.title}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}
                      </p>
                      {paper.arxiv_url && (
                        <p className="text-sm text-blue-600">{paper.arxiv_url}</p>
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
                      </div>
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
                        View Output
                      </button>
                    )}
                    <span className={getStatusBadgeClass(paper.status)}>
                      {paper.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="card">
            <div className="card-content">
              <p className="text-gray-600 text-center">
                Your processed papers will appear here. Start by processing your first paper!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
