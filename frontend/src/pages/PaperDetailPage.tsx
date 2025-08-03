import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Download, Eye, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { getPaper, downloadPaper, handleApiError, listPapers } from '@/services/api';
import { PaperMetadata } from '@/types';

export const PaperDetailPage: React.FC = () => {
  const { t } = useTranslation('pages');
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();
  const [paper, setPaper] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [isLoadingHtml, setIsLoadingHtml] = useState(false);

  useEffect(() => {
    if (paperId) {
      loadPaper();
    }
  }, [paperId]);

  const loadPaper = async () => {
    if (!paperId) return;

    try {
      setIsLoading(true);
      setError(null);
      
      // First get the paper list to find this paper's metadata
      const papersResponse = await listPapers(1, 100);
      const paperMetadata = papersResponse.papers.find((p: PaperMetadata) => p.paper_id === paperId);
      
      if (!paperMetadata) {
        setError(t('paperDetail.notFound'));
        return;
      }
      
      // Get detailed paper data
      const paperData = await getPaper(paperId);
      
      // Combine metadata with detailed data
      const fullPaperData = {
        ...paperData,
        metadata: paperMetadata
      };
      
      setPaper(fullPaperData);
      
      // If paper is completed, load the HTML content
      if (paperMetadata.status === 'completed') {
        await loadHtmlContent();
      }
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(t('paperDetail.loadFailed', { error: errorMessage }));
      console.error('Error loading paper:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHtmlContent = async () => {
    if (!paperId) return;

    try {
      setIsLoadingHtml(true);
      const blob = await downloadPaper(paperId, 'html');
      const text = await blob.text();
      setHtmlContent(text);
    } catch (err) {
      console.error('Error loading HTML content:', err);
      setError(t('paperDetail.contentLoadFailed'));
    } finally {
      setIsLoadingHtml(false);
    }
  };

  const handleDownload = async (format: 'html' | 'pdf' | 'json') => {
    if (!paperId || !paper) return;

    try {
      const blob = await downloadPaper(paperId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${paper.metadata?.title || 'paper'}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(t('paperDetail.downloads.failed', { format: format.toUpperCase(), error: errorMessage }));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/papers')}
            className="btn btn-outline btn-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('paperDetail.backToPapers')}
          </button>
        </div>
        
        <div className="card">
          <div className="card-content py-2">
            <div className="flex items-center justify-center space-x-2 text-gray-600 py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
              <p>{t('paperDetail.loading')}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/papers')}
            className="btn btn-outline btn-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('paperDetail.backToPapers')}
          </button>
        </div>
        
        <div className="card bg-red-50 border-red-200">
          <div className="card-content py-2">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <p>{error || 'Paper not found'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const metadata = paper.metadata as PaperMetadata;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/papers')}
            className="btn btn-outline btn-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Papers
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{t('paperDetail.title')}</h1>
        </div>
        
        {metadata.status === 'completed' && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDownload('html')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              {t('paperDetail.downloads.html')}
            </button>
            <button
              onClick={() => handleDownload('pdf')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              {t('paperDetail.downloads.pdf')}
            </button>
            <button
              onClick={() => handleDownload('json')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              {t('paperDetail.downloads.json')}
            </button>
          </div>
        )}
      </div>

      {/* Paper Metadata */}
      <div className="card">
        <div className="card-content py-2">
          <div className="flex items-start space-x-3">
            <FileText className="w-6 h-6 text-gray-400 mt-1" />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                {metadata.title}
              </h2>
              <p className="text-gray-600 mb-3">
                {Array.isArray(metadata.authors) ? metadata.authors.join(', ') : metadata.authors}
              </p>
              {metadata.arxiv_url && (
                <p className="text-blue-600 mb-3">
                  <a href={metadata.arxiv_url} target="_blank" rel="noopener noreferrer">
                    {metadata.arxiv_url}
                  </a>
                </p>
              )}
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <span>
                  {t('paperDetail.metadata.status')}<span className={`badge ${getStatusBadgeClass(metadata.status)} ml-1`}>
                    {metadata.status}
                  </span>
                </span>
                <span>{t('paperDetail.metadata.processed', { date: new Date(metadata.created_at).toLocaleDateString() })}</span>
                <span>{t('paperDetail.metadata.processingTime', { time: metadata.processing_time })}</span>
                <span>{t('paperDetail.metadata.format', { format: metadata.output_format, language: metadata.language })}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Processing Status Details */}
      {metadata.status !== 'completed' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Processing Status</h3>
          </div>
          <div className="card-content py-2">
            <div className="space-y-4">
              {/* Status Banner */}
              <div className={`p-4 rounded-lg border ${getStatusStyling(metadata.status)}`}>
                <div className="flex items-center space-x-3">
                  {getStatusIcon(metadata.status)}
                  <div className="flex-1">
                    <h4 className="font-medium">
                      {getStatusTitle(metadata.status)}
                    </h4>
                    <p className="text-sm opacity-75 mt-1">
                      {getStatusDescription(metadata.status)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Progress Bar for Non-Failed Status */}
              {metadata.status !== 'failed' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{getProgressPercentage(metadata.status)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${getProgressPercentage(metadata.status)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Error Details for Failed Papers */}
              {metadata.status === 'failed' && metadata.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <h5 className="font-medium text-red-800 mb-2">Error Details</h5>
                      <div className="text-sm text-red-700 font-mono bg-red-100 p-3 rounded border overflow-x-auto">
                        {metadata.error_message}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Retry Information */}
              {metadata.retry_count > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 text-orange-800">
                    <AlertCircle className="w-4 h-4" />
                    <span className="font-medium">Retry Information</span>
                  </div>
                  <div className="mt-2 text-sm text-orange-700">
                    <p>This paper has been retried {metadata.retry_count} time{metadata.retry_count > 1 ? 's' : ''}.</p>
                    {metadata.last_failed_at && (
                      <p className="mt-1">
                        Last failure: {new Date(metadata.last_failed_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Processing Timeline */}
              <div className="space-y-3">
                <h5 className="font-medium text-gray-900">Processing Timeline</h5>
                <div className="space-y-2">
                  {getProcessingSteps(metadata.status).map((step, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${step.completed ? 'bg-green-500' : step.current ? 'bg-blue-500' : 'bg-gray-300'}`} />
                      <span className={`text-sm ${step.completed ? 'text-green-700' : step.current ? 'text-blue-700' : 'text-gray-500'}`}>
                        {step.name}
                      </span>
                      {step.current && (
                        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Paper Content for Completed Papers */}
      {metadata.status === 'completed' && (
        <>
          {isLoadingHtml ? (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Generated Summary</h3>
              </div>
              <div className="card-content py-2">
                <div className="flex items-center justify-center space-x-2 text-gray-600 py-8">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <p>Loading content...</p>
                </div>
              </div>
            </div>
          ) : htmlContent ? (
            <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
          ) : (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Generated Summary</h3>
              </div>
              <div className="card-content py-2">
                <div className="p-6 text-center text-gray-600">
                  <Eye className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p>No content available</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );

  function getStatusBadgeClass(status: string) {
    switch (status) {
      case 'completed':
        return 'badge-success';
      case 'failed':
        return 'badge-error';
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
        return 'badge-warning';
      default:
        return 'badge-neutral';
    }
  }

  function getStatusStyling(status: string) {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'pending':
        return 'bg-gray-50 border-gray-200';
      case 'fetching':
      case 'fetching_arxiv':
      case 'fetching_content':
      case 'processing_images':
        return 'bg-blue-50 border-blue-200';
      case 'extracting':
      case 'extracting_structure':
      case 'extracting_content':
        return 'bg-purple-50 border-purple-200';
      case 'generating':
      case 'generating_html':
      case 'generating_pdf':
        return 'bg-orange-50 border-orange-200';
      case 'finalizing':
        return 'bg-indigo-50 border-indigo-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed':
        return <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
          <div className="w-2 h-2 bg-white rounded-full" />
        </div>;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'pending':
        return <div className="w-5 h-5 rounded-full bg-gray-400" />;
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
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      default:
        return <div className="w-5 h-5 rounded-full bg-gray-400" />;
    }
  }

  function getStatusTitle(status: string) {
    switch (status) {
      case 'completed':
        return 'Processing Completed';
      case 'failed':
        return 'Processing Failed';
      case 'pending':
        return 'Processing Queued';
      case 'fetching':
        return 'Fetching Paper Content';
      case 'fetching_arxiv':
        return 'Fetching from ArXiv';
      case 'fetching_content':
        return 'Processing Content';
      case 'processing_images':
        return 'Processing Images';
      case 'extracting':
        return 'Extracting Information';
      case 'extracting_structure':
        return 'Analyzing Structure';
      case 'extracting_content':
        return 'AI Content Extraction';
      case 'generating':
        return 'Generating Output';
      case 'generating_html':
        return 'Creating HTML Summary';
      case 'generating_pdf':
        return 'Creating PDF Version';
      case 'finalizing':
        return 'Finalizing Processing';
      default:
        return 'Processing...';
    }
  }

  function getStatusDescription(status: string) {
    switch (status) {
      case 'completed':
        return 'Your paper has been successfully processed and is ready for viewing.';
      case 'failed':
        return 'An error occurred during processing. Please check the error details below.';
      case 'pending':
        return 'Your paper is in the processing queue and will begin shortly.';
      case 'fetching':
        return 'Downloading and preparing the paper content for processing.';
      case 'fetching_arxiv':
        return 'Downloading the paper from ArXiv servers.';
      case 'fetching_content':
        return 'Processing and parsing the paper content.';
      case 'processing_images':
        return 'Downloading and processing embedded images and figures.';
      case 'extracting':
        return 'Using AI to extract and structure information from the paper.';
      case 'extracting_structure':
        return 'Analyzing the paper structure and identifying key sections.';
      case 'extracting_content':
        return 'Extracting detailed content using advanced AI models.';
      case 'generating':
        return 'Creating the final formatted output files.';
      case 'generating_html':
        return 'Generating the HTML summary with formatted content.';
      case 'generating_pdf':
        return 'Creating the PDF version of the summary.';
      case 'finalizing':
        return 'Saving metadata and finalizing the processing pipeline.';
      default:
        return 'Processing is in progress...';
    }
  }

  function getProgressPercentage(status: string) {
    switch (status) {
      case 'completed':
        return 100;
      case 'failed':
        return 0;
      case 'pending':
        return 5;
      case 'fetching':
        return 15;
      case 'fetching_arxiv':
        return 20;
      case 'fetching_content':
        return 25;
      case 'processing_images':
        return 30;
      case 'extracting':
        return 40;
      case 'extracting_structure':
        return 50;
      case 'extracting_content':
        return 65;
      case 'generating':
        return 75;
      case 'generating_html':
        return 85;
      case 'generating_pdf':
        return 90;
      case 'finalizing':
        return 95;
      default:
        return 0;
    }
  }

  function getProcessingSteps(currentStatus: string) {
    const steps = [
      { name: 'Queued for Processing', key: 'pending' },
      { name: 'Fetching Paper Content', key: 'fetching' },
      { name: 'Extracting Information', key: 'extracting' },
      { name: 'Generating Output', key: 'generating' },
      { name: 'Completed', key: 'completed' }
    ];

    // Map granular statuses to main categories
    const statusMapping: Record<string, string> = {
      'pending': 'pending',
      'fetching': 'fetching',
      'fetching_arxiv': 'fetching',
      'fetching_content': 'fetching',
      'processing_images': 'fetching',
      'extracting': 'extracting',
      'extracting_structure': 'extracting',
      'extracting_content': 'extracting',
      'generating': 'generating',
      'generating_html': 'generating',
      'generating_pdf': 'generating',
      'finalizing': 'generating',
      'completed': 'completed',
      'failed': 'failed'
    };

    const mappedStatus = statusMapping[currentStatus] || 'pending';
    const statusOrder = ['pending', 'fetching', 'extracting', 'generating', 'completed'];
    const currentIndex = statusOrder.indexOf(mappedStatus);
    
    return steps.map((step, index) => ({
      ...step,
      completed: index < currentIndex || (mappedStatus === 'completed' && index === steps.length - 1),
      current: index === currentIndex && currentStatus !== 'failed' && currentStatus !== 'completed'
    }));
  }
};
