import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Upload, Link, Loader2, AlertCircle, Globe } from 'lucide-react';
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
  UploadedFile,
  ProcessPaperResponse 
} from '@/types';

export const ProcessPaperPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation(['pages', 'common']);
  const [inputType, setInputType] = useState<'url' | 'file'>('url');
  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<'en' | 'zh'>('en');
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
        console.log('Starting file upload...');
        uploadedFileData = await uploadFile(selectedFile, (progress) => {
          setUploadProgress(progress);
        });
        setUploadProgress(100);
        console.log('File upload completed:', uploadedFileData);
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
        language: selectedLanguage,
        save_json: true
      };
      
      console.log('Sending paper processing request:', request);
      
      // Step 4: Start paper processing with detailed logging
      let response: ProcessPaperResponse;
      try {
        const apiResponse = await processPaper(request);
        console.log('Received response from processPaper:', apiResponse);
        
        // Validate response structure
        if (!apiResponse || typeof apiResponse !== 'object') {
          throw new Error('Invalid response format: response is not an object');
        }
        
        // Check if it's a valid response type
        if (!apiResponse.status) {
          throw new Error('Invalid response format: missing status field');
        }
        
        response = apiResponse as ProcessPaperResponse;
        console.log('Successfully parsed response:', response);
      } catch (apiError: any) {
        console.error('Error in processPaper API call:', apiError);
        // Add more specific error information
        if (apiError.code === 'ECONNABORTED') {
          throw new Error('Request timed out. Please check your connection and try again.');
        } else if (apiError.response) {
          console.error('API response error:', {
            status: apiError.response.status,
            statusText: apiError.response.statusText,
            data: apiError.response.data
          });
          throw new Error(`Server error (${apiError.response.status}): ${handleApiError(apiError)}`);
        } else if (apiError.request) {
          console.error('Network error - no response received:', apiError.request);
          throw new Error('Network error: Unable to reach the server. Please check your connection.');
        } else {
          throw apiError; // Re-throw original error
        }
      }
      
      // Handle different response types
      if (response.status === 'duplicate_found') {
        console.log('Duplicate paper found:', (response as any).duplicate_paper);
        // Show duplicate paper notification and navigate to papers page
        setError(null);
        setIsProcessing(false);
        
        // Reset form
        setInputValue('');
        setSelectedFile(null);
        setUploadProgress(0);
        
        // Navigate to papers page with duplicate notification
        navigate('/papers', {
          state: {
            duplicateFound: true,
            duplicatePaper: (response as any).duplicate_paper,
            originalInput: inputValue
          }
        });
        return;
      }
      
      // Handle processing_started response
      if (response.status === 'processing_started') {
        const processingResponse = response as any;
        if (!processingResponse.paper_id) {
          throw new Error('Invalid response: missing paper_id for processing_started status');
        }
        
        console.log('Processing started successfully for paper:', processingResponse.paper_id);
        
        // Reset form after successful submission
        setInputValue('');
        setSelectedFile(null);
        setUploadProgress(0);
        
        // Navigate to papers page immediately after successful submission
        navigate('/papers', { 
          state: { 
            newPaperId: processingResponse.paper_id,
            showProcessing: true 
          } 
        });
      } else {
        console.warn('Unexpected response status:', (response as any).status);
        throw new Error(`Unexpected response status: ${(response as any).status}`);
      }
      
    } catch (err) {
      console.error('Error in handleProcessPaper:', err);
      const errorMessage = handleApiError(err);
      setError(`Processing failed: ${errorMessage}`);
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
        <h1 className="text-2xl font-bold text-gray-900">{t('pages:processPaper.title')}</h1>
        <p className="text-gray-600 mt-2">
          {t('pages:processPaper.subtitle')}
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">{t('pages:processPaper.inputSection.title')}</h3>
          <p className="card-description">
            {t('pages:processPaper.inputSection.description')}
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
              {t('common:buttons.upload')}
            </button>
          </div>

          {/* Input Field */}
          {inputType === 'url' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('pages:processPaper.urlInput.label')}
              </label>
              <input
                type="url"
                className="input"
                placeholder={t('pages:processPaper.urlInput.placeholder')}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('pages:processPaper.fileInput.label')}
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  onChange={handleFileSelect}
                />
                <div className="dropzone">
                  <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600">
                    {selectedFile ? selectedFile.name : t('pages:processPaper.fileInput.placeholder')}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Language Selection */}
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700 flex items-center">
              <Globe className="w-4 h-4 mr-2" />
              {t('pages:processPaper.languageSection.title')}:
            </label>
            <select
              className="input flex-shrink-0 w-auto min-w-[120px]"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value as 'en' | 'zh')}
            >
              <option value="en">{t('pages:processPaper.languageOptions.en')}</option>
              <option value="zh">{t('pages:processPaper.languageOptions.zh')}</option>
            </select>
          </div>

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
                  {t('common:buttons.processing')}
                </>
              ) : (
                t('common:buttons.processPaper')
              )}
            </button>
            <button
              className="btn-outline btn-md"
              onClick={() => navigate('/papers')}
            >
              {t('common:buttons.viewPapers')}
            </button>
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

      {/* Upload Progress */}
      {inputType === 'file' && uploadProgress > 0 && uploadProgress < 100 && (
        <div className="card">
          <div className="card-content py-2">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{t('pages:processPaper.uploadProgress')}</span>
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
          <div className="card-content py-2">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">{t('pages:processPaper.processingProgress')}</h3>
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
                  {t('pages:processPaper.processingCompleted')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
