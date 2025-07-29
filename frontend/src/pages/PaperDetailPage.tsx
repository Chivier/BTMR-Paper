import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Eye, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { getPaper, downloadPaper, handleApiError, listPapers } from '@/services/api';
import { PaperMetadata } from '@/types';

export const PaperDetailPage: React.FC = () => {
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
        setError('Paper not found');
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
      setError(`Failed to load paper: ${errorMessage}`);
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
      setError('Failed to load paper content');
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
      setError(`Failed to download ${format.toUpperCase()}: ${errorMessage}`);
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
            Back to Papers
          </button>
        </div>
        
        <div className="card">
          <div className="card-content">
            <div className="flex items-center justify-center space-x-2 text-gray-600 py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
              <p>Loading paper...</p>
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
            Back to Papers
          </button>
        </div>
        
        <div className="card bg-red-50 border-red-200">
          <div className="card-content">
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
          <h1 className="text-2xl font-bold text-gray-900">Paper Details</h1>
        </div>
        
        {metadata.status === 'completed' && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDownload('html')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              HTML
            </button>
            <button
              onClick={() => handleDownload('pdf')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              PDF
            </button>
            <button
              onClick={() => handleDownload('json')}
              className="btn btn-outline btn-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              JSON
            </button>
          </div>
        )}
      </div>

      {/* Paper Metadata */}
      <div className="card">
        <div className="card-content">
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
                  Status: <span className={`badge ${getStatusBadgeClass(metadata.status)} ml-1`}>
                    {metadata.status}
                  </span>
                </span>
                <span>Processed: {new Date(metadata.created_at).toLocaleDateString()}</span>
                <span>Processing Time: {metadata.processing_time}s</span>
                <span>Format: {metadata.output_format} • {metadata.language}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Paper Content */}
      {metadata.status === 'completed' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Generated Summary</h3>
          </div>
          <div className="card-content p-0">
            {isLoadingHtml ? (
              <div className="flex items-center justify-center space-x-2 text-gray-600 py-8">
                <Loader2 className="w-5 h-5 animate-spin" />
                <p>Loading content...</p>
              </div>
            ) : htmlContent ? (
              <iframe
                srcDoc={htmlContent}
                className="w-full border-0"
                style={{ minHeight: '800px', height: '80vh' }}
                title="Paper Summary"
                sandbox="allow-same-origin allow-scripts"
              />
            ) : (
              <div className="p-6 text-center text-gray-600">
                <Eye className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No content available</p>
              </div>
            )}
          </div>
        </div>
      )}

      {metadata.status !== 'completed' && (
        <div className="card">
          <div className="card-content">
            <div className="text-center py-8">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Paper {metadata.status === 'failed' ? 'Processing Failed' : 'Still Processing'}
              </h3>
              <p className="text-gray-600">
                {metadata.status === 'failed' 
                  ? 'The paper processing failed. Please try processing it again.'
                  : 'The paper is still being processed. Please check back later.'
                }
              </p>
            </div>
          </div>
        </div>
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
      case 'extracting':
      case 'generating':
        return 'badge-warning';
      default:
        return 'badge-neutral';
    }
  }
};
