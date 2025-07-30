import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Link, Loader2, AlertCircle } from 'lucide-react';
import { 
  processPaper, 
  uploadFile, 
  createProgressWebSocket, 
  handleApiError,
  isValidArxivUrl,
  isValidUrl
} from '@/services/api';
import { 
  PaperProcessRequest, 
  ProcessingProgress, 
  UploadedFile 
} from '@/types';

export const ProcessPaperPage: React.FC = () => {
  const navigate = useNavigate();
  const [inputType, setInputType] = useState<'url' | 'file'>('url');
  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeWebSocket, setActiveWebSocket] = useState<WebSocket | null>(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (activeWebSocket) {
        activeWebSocket.close();
      }
    };
  }, [activeWebSocket]);

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
      
      // Reset form after successful submission
      setInputValue('');
      setSelectedFile(null);
      setUploadProgress(0);
      
      // Navigate to papers page immediately after successful submission
      navigate('/papers', { 
        state: { 
          newPaperId: paperId,
          showProcessing: true 
        } 
      });
      
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Process New Paper</h1>
        <p className="text-gray-600 mt-2">
          Upload a PDF file or provide a URL to an academic paper for AI-powered extraction and summarization.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Paper Input</h3>
          <p className="card-description">
            Choose how you want to provide the paper for processing
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
              onClick={() => navigate('/papers')}
            >
              View Papers
            </button>
          </div>
        </div>
      </div>

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
              {processingProgress.status === 'completed' && (
                <p className="text-sm text-green-600 mt-2">
                  Processing completed! Redirecting to papers page...
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
