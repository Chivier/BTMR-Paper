import React, { useState, useEffect } from 'react';
import {
  ConfigurationResponse,
  ConfigurationRequest,
  ConfigurationValidation,
  AvailableModelsResponse,
  LoadingState,
} from '@/types';
import {
  getConfiguration,
  updateConfiguration,
  resetConfiguration,
  validateConfiguration,
  getAvailableModels,
  handleApiError,
} from '@/services/api';
import { useNotification } from '@/context/NotificationContext';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<ConfigurationResponse | null>(null);
  const [validation, setValidation] = useState<ConfigurationValidation | null>(null);
  const [availableModels, setAvailableModels] = useState<AvailableModelsResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [modelsLoadingState, setModelsLoadingState] = useState<LoadingState>('idle');
  const [saveState, setSaveState] = useState<LoadingState>('idle');
  const [reloadingModels, setReloadingModels] = useState<LoadingState>('idle');
  const [saveProgress, setSaveProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'api' | 'processing' | 'image' | 'system'>('api');
  const [useCustomDefaultModel, setUseCustomDefaultModel] = useState<boolean>(false);
  const [useCustomTranslateModel, setUseCustomTranslateModel] = useState<boolean>(false);

  const { showNotification } = useNotification();

  // Form state
  const [formData, setFormData] = useState<ConfigurationRequest>({});

  useEffect(() => {
    loadConfiguration();
    loadAvailableModels();
  }, []);

  // Effect to check if current models are custom (not in available models list)
  useEffect(() => {
    if (availableModels && formData.default_model) {
      const isDefaultModelInList = availableModels.models.some(model => model.id === formData.default_model);
      setUseCustomDefaultModel(!isDefaultModelInList);
    }
    if (availableModels && formData.translate_model) {
      const isTranslateModelInList = availableModels.models.some(model => model.id === formData.translate_model);
      setUseCustomTranslateModel(!isTranslateModelInList);
    }
  }, [availableModels, formData.default_model, formData.translate_model]);

  const loadConfiguration = async () => {
    setLoadingState('loading');
    setError(null);
    
    try {
      const [configData, validationData] = await Promise.all([
        getConfiguration(),
        validateConfiguration(),
      ]);
      
      setConfig(configData);
      setValidation(validationData);
      
      // Initialize form data
      setFormData({
        openai_api_key: configData.openai_api_key,
        openai_api_base: configData.openai_api_base,
        default_model: configData.default_model,
        translate_model: configData.translate_model,
        max_paper_length: configData.max_paper_length,
        max_image_size_mb: configData.max_image_size_mb,
        request_timeout: configData.request_timeout,
        default_output_format: configData.default_output_format,
        default_language: configData.default_language,
        image_quality: configData.image_quality,
        max_image_dimension: configData.max_image_dimension,
        log_level: configData.log_level,
      });
      
      setLoadingState('success');
    } catch (err) {
      setError(handleApiError(err));
      setLoadingState('error');
    }
  };

  const loadAvailableModels = async (useFormData: boolean = true) => {
    setModelsLoadingState('loading');
    
    try {
      // Use form data for real-time preview, or saved config for post-save refresh
      const apiKey = useFormData ? formData.openai_api_key : config?.openai_api_key;
      const apiBase = useFormData ? formData.openai_api_base : config?.openai_api_base;
      
      const models = await getAvailableModels(apiKey, apiBase, showNotification);
      setAvailableModels(models);
      setModelsLoadingState('success');
    } catch (err) {
      // Set fallback models in case of complete failure
      setAvailableModels({
        models: [],
        custom_note: 'Failed to load models. Please check your API configuration.',
        error: 'Network error'
      });
      setModelsLoadingState('error');
    }
  };

  const handleReloadModels = async () => {
    setReloadingModels('loading');
    setError(null);
    setSuccessMessage(null);

    try {
      // First save the current form data if there are changes
      const updates: ConfigurationRequest = {};
      
      if (formData.openai_api_key !== config?.openai_api_key) {
        updates.openai_api_key = formData.openai_api_key;
      }
      if (formData.openai_api_base !== config?.openai_api_base) {
        updates.openai_api_base = formData.openai_api_base;
      }
      if (formData.default_model !== config?.default_model) {
        updates.default_model = formData.default_model;
      }
      if (formData.translate_model !== config?.translate_model) {
        updates.translate_model = formData.translate_model;
      }
      if (formData.max_paper_length !== config?.max_paper_length) {
        updates.max_paper_length = formData.max_paper_length;
      }
      if (formData.max_image_size_mb !== config?.max_image_size_mb) {
        updates.max_image_size_mb = formData.max_image_size_mb;
      }
      if (formData.request_timeout !== config?.request_timeout) {
        updates.request_timeout = formData.request_timeout;
      }
      if (formData.default_output_format !== config?.default_output_format) {
        updates.default_output_format = formData.default_output_format;
      }
      if (formData.default_language !== config?.default_language) {
        updates.default_language = formData.default_language;
      }
      if (formData.image_quality !== config?.image_quality) {
        updates.image_quality = formData.image_quality;
      }
      if (formData.max_image_dimension !== config?.max_image_dimension) {
        updates.max_image_dimension = formData.max_image_dimension;
      }
      if (formData.log_level !== config?.log_level) {
        updates.log_level = formData.log_level;
      }

      // Save configuration if there are changes
      if (Object.keys(updates).length > 0) {
        const updatedConfig = await updateConfiguration(updates);
        setConfig(updatedConfig);
        
        // Refresh validation
        const newValidation = await validateConfiguration();
        setValidation(newValidation);
      }
      
      // Now reload models with the saved configuration
      await loadAvailableModels(false);
      
      setSuccessMessage('Models reloaded successfully');
      setReloadingModels('success');
      
    } catch (err) {
      setError(handleApiError(err));
      setReloadingModels('error');
    }
  };

  const handleSave = async () => {
    setSaveState('loading');
    setSaveProgress('Saving configuration...');
    setError(null);
    setSuccessMessage(null);

    try {
      // Filter out unchanged values
      const updates: ConfigurationRequest = {};
      
      if (formData.openai_api_key !== config?.openai_api_key) {
        updates.openai_api_key = formData.openai_api_key;
      }
      if (formData.openai_api_base !== config?.openai_api_base) {
        updates.openai_api_base = formData.openai_api_base;
      }
      if (formData.default_model !== config?.default_model) {
        updates.default_model = formData.default_model;
      }
      if (formData.translate_model !== config?.translate_model) {
        updates.translate_model = formData.translate_model;
      }
      if (formData.max_paper_length !== config?.max_paper_length) {
        updates.max_paper_length = formData.max_paper_length;
      }
      if (formData.max_image_size_mb !== config?.max_image_size_mb) {
        updates.max_image_size_mb = formData.max_image_size_mb;
      }
      if (formData.request_timeout !== config?.request_timeout) {
        updates.request_timeout = formData.request_timeout;
      }
      if (formData.default_output_format !== config?.default_output_format) {
        updates.default_output_format = formData.default_output_format;
      }
      if (formData.default_language !== config?.default_language) {
        updates.default_language = formData.default_language;
      }
      if (formData.image_quality !== config?.image_quality) {
        updates.image_quality = formData.image_quality;
      }
      if (formData.max_image_dimension !== config?.max_image_dimension) {
        updates.max_image_dimension = formData.max_image_dimension;
      }
      if (formData.log_level !== config?.log_level) {
        updates.log_level = formData.log_level;
      }

      if (Object.keys(updates).length === 0) {
        setSuccessMessage('No changes to save');
        setSaveState('success');
        setSaveProgress('');
        return;
      }

      const updatedConfig = await updateConfiguration(updates);
      setConfig(updatedConfig);
      
      // Refresh validation
      setSaveProgress('Validating configuration...');
      const newValidation = await validateConfiguration();
      setValidation(newValidation);
      
      setSuccessMessage('Configuration saved successfully');
      setSaveState('success');
      setSaveProgress('');
      
    } catch (err) {
      setError(handleApiError(err));
      setSaveState('error');
      setSaveProgress('');
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
      return;
    }

    setSaveState('loading');
    setError(null);
    setSuccessMessage(null);

    try {
      const resetConfig = await resetConfiguration();
      setConfig(resetConfig);
      setFormData({
        openai_api_key: resetConfig.openai_api_key,
        openai_api_base: resetConfig.openai_api_base,
        default_model: resetConfig.default_model,
        translate_model: resetConfig.translate_model,
        max_paper_length: resetConfig.max_paper_length,
        max_image_size_mb: resetConfig.max_image_size_mb,
        request_timeout: resetConfig.request_timeout,
        default_output_format: resetConfig.default_output_format,
        default_language: resetConfig.default_language,
        image_quality: resetConfig.image_quality,
        max_image_dimension: resetConfig.max_image_dimension,
        log_level: resetConfig.log_level,
      });
      
      // Reset toggle states - they will be updated by the useEffect
      setUseCustomDefaultModel(false);
      setUseCustomTranslateModel(false);
      setSuccessMessage('Configuration reset to defaults');
      setSaveState('success');
      
      // Refresh validation
      const newValidation = await validateConfiguration();
      setValidation(newValidation);
      
    } catch (err) {
      setError(handleApiError(err));
      setSaveState('error');
    }
  };

  const updateFormField = (field: keyof ConfigurationRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
  };

  if (loadingState === 'loading') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <div className="card">
          <div className="card-content py-2">
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading configuration...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loadingState === 'error') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <div className="card">
          <div className="card-content py-2">
            <div className="text-center py-8">
              <div className="text-red-600 mb-4">Failed to load configuration</div>
              <p className="text-gray-600 mb-4">{error}</p>
              <button
                onClick={loadConfiguration}
                className="btn btn-primary"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <div className="flex space-x-3">
            <button
            onClick={handleReset}
            disabled={saveState === 'loading'}
            className="btn btn-secondary px-3 py-3"
            >
            {saveState === 'loading' ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                Resetting...
              </div>
            ) : (
              'Reset to Defaults'
            )}
          </button>
          <button
            onClick={handleSave}
            disabled={saveState === 'loading'}
            className="btn btn-primary px-3 py-3"
          >
            {saveState === 'loading' ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {saveProgress || 'Saving...'}
              </div>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="text-green-800">{successMessage}</div>
        </div>
      )}

      {/* Validation Status */}
      {validation && (
        <div className={`border rounded-md p-4 ${
          validation.valid 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className={`font-medium ${
            validation.valid ? 'text-green-800' : 'text-yellow-800'
          }`}>
            Configuration Status: {validation.valid ? 'Valid' : 'Issues Found'}
          </div>
          
          {validation.issues.length > 0 && (
            <div className="mt-2">
              <div className="text-red-800 font-medium">Issues:</div>
              <ul className="list-disc list-inside text-red-700">
                {validation.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          
          {validation.warnings.length > 0 && (
            <div className="mt-2">
              <div className="text-yellow-800 font-medium">Warnings:</div>
              <ul className="list-disc list-inside text-yellow-700">
                {validation.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'api' as const, label: 'API Settings' },
            { id: 'processing' as const, label: 'Processing' },
            { id: 'image' as const, label: 'Image Settings' },
            { id: 'system' as const, label: 'System' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="card">
        <div className="card-content py-2">
          {activeTab === 'api' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">API Configuration</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  OpenAI API Key
                </label>
                <input
                  type="password"
                  value={formData.openai_api_key || ''}
                  onChange={(e) => updateFormField('openai_api_key', e.target.value)}
                  className="input w-full"
                  placeholder="sk-..."
                />
                <p className="text-sm text-gray-500 mt-1">
                  Your OpenAI API key for accessing GPT models
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Base URL
                </label>
                <input
                  type="url"
                  value={formData.openai_api_base || ''}
                  onChange={(e) => updateFormField('openai_api_base', e.target.value)}
                  className="input w-full"
                  placeholder="https://api.openai.com/v1"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Custom API endpoint (leave default for OpenAI)
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Default Model
                  </label>
                  <div className="flex items-center space-x-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={useCustomDefaultModel}
                        onChange={(e) => setUseCustomDefaultModel(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-600">Use custom model ID</span>
                    </label>
                    <button
                      onClick={handleReloadModels}
                      disabled={reloadingModels === 'loading' || modelsLoadingState === 'loading'}
                      className="btn btn-sm btn-secondary flex items-center"
                      title="Save configuration and reload models"
                    >
                      {(reloadingModels === 'loading' || modelsLoadingState === 'loading') ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-1"></div>
                      ) : (
                        <span className="mr-1">🔄</span>
                      )}
                      {reloadingModels === 'loading' ? 'Reloading...' : 'Reload Models'}
                    </button>
                  </div>
                </div>
                
                {useCustomDefaultModel ? (
                  <input
                    type="text"
                    value={formData.default_model || ''}
                    onChange={(e) => updateFormField('default_model', e.target.value)}
                    className="input w-full"
                    placeholder="Enter custom model ID (e.g., gpt-4, claude-3-sonnet, etc.)"
                  />
                ) : (
                  <select
                    value={formData.default_model || ''}
                    onChange={(e) => updateFormField('default_model', e.target.value)}
                    disabled={modelsLoadingState === 'loading'}
                    className={`input w-full ${modelsLoadingState === 'loading' ? 'bg-gray-100' : ''}`}
                  >
                    {modelsLoadingState === 'loading' ? (
                      <option value="">Loading models...</option>
                    ) : availableModels?.error ? (
                      <option value="">Failed to load models</option>
                    ) : (
                      availableModels?.models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.id} {model.recommended ? '(Recommended)' : ''}
                        </option>
                      ))
                    )}
                  </select>
                )}
                
                <p className="text-sm text-gray-500 mt-1">
                  {useCustomDefaultModel 
                    ? 'Enter a custom model ID that your API provider supports'
                    : 'Default model for paper processing'
                  }
                </p>
                {availableModels?.error && !useCustomDefaultModel && (
                  <p className="text-sm text-red-600 mt-1">
                    Error: {availableModels.error}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Translation Model
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={useCustomTranslateModel}
                      onChange={(e) => setUseCustomTranslateModel(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-600">Use custom model ID</span>
                  </label>
                </div>
                
                {useCustomTranslateModel ? (
                  <input
                    type="text"
                    value={formData.translate_model || ''}
                    onChange={(e) => updateFormField('translate_model', e.target.value)}
                    className="input w-full"
                    placeholder="Enter custom model ID (e.g., gpt-4, claude-3-sonnet, etc.)"
                  />
                ) : (
                  <select
                    value={formData.translate_model || ''}
                    onChange={(e) => updateFormField('translate_model', e.target.value)}
                    disabled={modelsLoadingState === 'loading'}
                    className={`input w-full ${modelsLoadingState === 'loading' ? 'bg-gray-100' : ''}`}
                  >
                    {modelsLoadingState === 'loading' ? (
                      <option value="">Loading models...</option>
                    ) : availableModels?.error ? (
                      <option value="">Failed to load models</option>
                    ) : (
                      availableModels?.models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.id} {model.recommended ? '(Recommended)' : ''}
                        </option>
                      ))
                    )}
                  </select>
                )}
                
                <p className="text-sm text-gray-500 mt-1">
                  {useCustomTranslateModel 
                    ? 'Enter a custom model ID that your API provider supports'
                    : 'Model used for translation tasks'
                  }
                </p>
                {availableModels?.error && !useCustomTranslateModel && (
                  <p className="text-sm text-red-600 mt-1">
                    Error: {availableModels.error}
                  </p>
                )}
              </div>

            </div>
          )}

          {activeTab === 'processing' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Processing Settings</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Paper Length (characters)
                </label>
                <input
                  type="number"
                  min="1000"
                  max="200000"
                  value={formData.max_paper_length || ''}
                  onChange={(e) => updateFormField('max_paper_length', parseInt(e.target.value))}
                  className="input w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Maximum characters to send to LLM (1,000 - 200,000)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Request Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={formData.request_timeout || ''}
                  onChange={(e) => updateFormField('request_timeout', parseInt(e.target.value))}
                  className="input w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  HTTP request timeout (5 - 300 seconds)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Output Format
                </label>
                <select
                  value={formData.default_output_format || ''}
                  onChange={(e) => updateFormField('default_output_format', e.target.value)}
                  className="input w-full"
                >
                  <option value="html">HTML</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Language
                </label>
                <select
                  value={formData.default_language || ''}
                  onChange={(e) => updateFormField('default_language', e.target.value)}
                  className="input w-full"
                >
                  <option value="en">English</option>
                  <option value="zh">Chinese</option>
                </select>
              </div>
            </div>
          )}

          {activeTab === 'image' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Image Processing</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Image Size (MB)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="100"
                  step="0.1"
                  value={formData.max_image_size_mb || ''}
                  onChange={(e) => updateFormField('max_image_size_mb', parseFloat(e.target.value))}
                  className="input w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Maximum image file size (0.1 - 100 MB)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Image Quality (1-100)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.image_quality || ''}
                  onChange={(e) => updateFormField('image_quality', parseInt(e.target.value))}
                  className="input w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  JPEG compression quality (higher = better quality, larger files)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Image Dimension (pixels)
                </label>
                <input
                  type="number"
                  min="100"
                  max="5000"
                  value={formData.max_image_dimension || ''}
                  onChange={(e) => updateFormField('max_image_dimension', parseInt(e.target.value))}
                  className="input w-full"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Maximum width/height for images (100 - 5,000 pixels)
                </p>
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">System Settings</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Log Level
                </label>
                <select
                  value={formData.log_level || ''}
                  onChange={(e) => updateFormField('log_level', e.target.value)}
                  className="input w-full"
                >
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  Application logging level
                </p>
              </div>

              {config?.colors && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Color Scheme
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(config.colors).map(([key, color]) => (
                      <div key={key} className="flex items-center space-x-3">
                        <div
                          className="w-6 h-6 rounded border"
                          style={{ backgroundColor: color }}
                        ></div>
                        <span className="text-sm capitalize">{key}</span>
                        <span className="text-sm text-gray-500">{color}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-gray-50 rounded-md p-4">
                <h4 className="font-medium text-gray-900 mb-2">Configuration Files</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>Environment file (.env)</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      validation?.env_file_exists 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {validation?.env_file_exists ? 'Exists' : 'Not found'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Config file (config.json)</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      validation?.config_file_exists 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {validation?.config_file_exists ? 'Exists' : 'Not found'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
