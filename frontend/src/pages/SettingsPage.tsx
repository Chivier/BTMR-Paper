import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  testModel,
  handleApiError,
} from '@/services/api';
import { useNotification } from '@/context/NotificationContext';

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation(['pages', 'common']);
  const [config, setConfig] = useState<ConfigurationResponse | null>(null);
  const [validation, setValidation] = useState<ConfigurationValidation | null>(null);
  const [availableModels, setAvailableModels] = useState<AvailableModelsResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [modelsLoadingState, setModelsLoadingState] = useState<LoadingState>('idle');
  const [saveState, setSaveState] = useState<LoadingState>('idle');
  const [reloadingModels, setReloadingModels] = useState<LoadingState>('idle');
  const [testingModel, setTestingModel] = useState<LoadingState>('idle');
  const [modelTestResult, setModelTestResult] = useState<any | null>(null);
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

  const loadAvailableModels = async () => {
    setModelsLoadingState('loading');
    
    try {
      const models = await getAvailableModels(showNotification);
      setAvailableModels(models);
      setModelsLoadingState('success');
    } catch (err) {
      // Set fallback models in case of complete failure
      setAvailableModels({
        models: [],
        custom_note: t('pages:settings.messages.failedToLoadModelsNote'),
        error: t('pages:settings.messages.networkError')
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
      await loadAvailableModels();
      
      setSuccessMessage(t('pages:settings.messages.modelsReloaded'));
      setReloadingModels('success');
      
    } catch (err) {
      setError(handleApiError(err));
      setReloadingModels('error');
    }
  };

  const handleSave = async () => {
    setSaveState('loading');
    setSaveProgress(t('pages:settings.messages.savingConfiguration'));
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
        setSuccessMessage(t('pages:settings.messages.noChangesToSave'));
        setSaveState('success');
        setSaveProgress('');
        return;
      }

      const updatedConfig = await updateConfiguration(updates);
      setConfig(updatedConfig);
      
      // Refresh validation
      setSaveProgress(t('pages:settings.messages.validatingConfiguration'));
      const newValidation = await validateConfiguration();
      setValidation(newValidation);
      
      setSuccessMessage(t('pages:settings.messages.configurationSaved'));
      setSaveState('success');
      setSaveProgress('');
      
    } catch (err) {
      setError(handleApiError(err));
      setSaveState('error');
      setSaveProgress('');
    }
  };

  const handleReset = async () => {
    if (!confirm(t('pages:settings.messages.confirmReset'))) {
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
      setSuccessMessage(t('pages:settings.messages.configurationReset'));
      setSaveState('success');
      
      // Refresh validation
      const newValidation = await validateConfiguration();
      setValidation(newValidation);
      
    } catch (err) {
      setError(handleApiError(err));
      setSaveState('error');
    }
  };

  const handleTestModel = async () => {
    if (!formData.default_model) {
      setError(t('pages:settings.messages.pleaseSelectModel'));
      return;
    }

    setTestingModel('loading');
    setError(null);
    setSuccessMessage(null);
    setModelTestResult(null);

    try {
      const result = await testModel(formData.default_model);
      
      setModelTestResult(result);
      
      if (result.available) {
        setSuccessMessage(t('pages:settings.messages.modelAvailable', { model: formData.default_model }));
        showNotification(t('pages:settings.messages.modelTestSuccessful', { model: formData.default_model }), 'success');
      } else {
        setError(t('pages:settings.messages.modelTestFailed', { error: result.error }));
        showNotification(t('pages:settings.messages.modelTestFailed', { error: result.error }), 'error');
      }
      
      setTestingModel('success');
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(t('pages:settings.messages.failedToTestModel', { error: errorMessage }));
      showNotification(t('pages:settings.messages.failedToTestModel', { error: errorMessage }), 'error');
      setTestingModel('error');
    }
  };

  const updateFormField = (field: keyof ConfigurationRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
  };

  if (loadingState === 'loading') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('pages:settings.title')}</h1>
        <div className="card">
          <div className="card-content py-2">
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">{t('pages:settings.messages.loadingConfiguration')}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loadingState === 'error') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('pages:settings.title')}</h1>
        <div className="card">
          <div className="card-content py-2">
            <div className="text-center py-8">
              <div className="text-red-600 mb-4">{t('pages:settings.messages.failedToLoad')}</div>
              <p className="text-gray-600 mb-4">{error}</p>
              <button
                onClick={loadConfiguration}
                className="btn btn-primary"
              >
                {t('common:buttons.retry')}
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
        <h1 className="text-2xl font-bold text-gray-900">{t('pages:settings.title')}</h1>
        <div className="flex space-x-3">
            <button
            onClick={handleReset}
            disabled={saveState === 'loading'}
            className="btn btn-secondary px-3 py-3"
            >
            {saveState === 'loading' ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                {t('pages:settings.messages.resetting')}
              </div>
            ) : (
              t('common:buttons.resetToDefaults')
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
                {saveProgress || t('common:buttons.saving')}
              </div>
            ) : (
              t('common:buttons.saveChanges')
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
            {t('pages:settings.status.configurationStatus')}: {validation.valid ? t('pages:settings.status.valid') : t('pages:settings.status.issuesFound')}
          </div>
          
          {validation.issues.length > 0 && (
            <div className="mt-2">
              <div className="text-red-800 font-medium">{t('pages:settings.status.issues')}:</div>
              <ul className="list-disc list-inside text-red-700">
                {validation.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          
          {validation.warnings.length > 0 && (
            <div className="mt-2">
              <div className="text-yellow-800 font-medium">{t('pages:settings.status.warnings')}:</div>
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
            { id: 'api' as const, label: t('pages:settings.tabs.api') },
            { id: 'processing' as const, label: t('pages:settings.tabs.processing') },
            { id: 'image' as const, label: t('pages:settings.tabs.image') },
            { id: 'system' as const, label: t('pages:settings.tabs.system') },
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
              <h3 className="text-lg font-medium text-gray-900">{t('pages:settings.api.title')}</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.api.openaiApiKey.label')}
                </label>
                <input
                  type="password"
                  value={formData.openai_api_key || ''}
                  onChange={(e) => updateFormField('openai_api_key', e.target.value)}
                  className="input w-full"
                  placeholder={t('pages:settings.api.openaiApiKey.placeholder')}
                />
                <p className="text-sm text-gray-500 mt-1">
                  {t('pages:settings.api.openaiApiKey.description')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.api.apiBaseUrl.label')}
                </label>
                <input
                  type="url"
                  value={formData.openai_api_base || ''}
                  onChange={(e) => updateFormField('openai_api_base', e.target.value)}
                  className="input w-full"
                  placeholder={t('pages:settings.api.apiBaseUrl.placeholder')}
                />
                <p className="text-sm text-gray-500 mt-1">
                  {t('pages:settings.api.apiBaseUrl.description')}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    {t('pages:settings.api.defaultModel.label')}
                  </label>
                  <div className="flex items-center space-x-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={useCustomDefaultModel}
                        onChange={(e) => setUseCustomDefaultModel(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-600">{t('pages:settings.api.defaultModel.useCustom')}</span>
                    </label>
                    <button
                      onClick={handleReloadModels}
                      disabled={reloadingModels === 'loading' || modelsLoadingState === 'loading'}
                      className="btn btn-sm btn-secondary flex items-center"
                      title={t('pages:settings.messages.reloadModelsTooltip')}
                    >
                      {(reloadingModels === 'loading' || modelsLoadingState === 'loading') ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-1"></div>
                      ) : (
                        <span className="mr-1">🔄</span>
                      )}
                      {reloadingModels === 'loading' ? t('pages:settings.messages.reloading') : t('common:buttons.reloadModels')}
                    </button>
                    <button
                      onClick={handleTestModel}
                      disabled={testingModel === 'loading' || !formData.default_model}
                      className="btn btn-sm btn-primary flex items-center"
                      title={t('pages:settings.messages.testModelTooltip')}
                    >
                      {testingModel === 'loading' ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                      ) : (
                        <span className="mr-1">🧪</span>
                      )}
                      {testingModel === 'loading' ? t('common:status.testing') : t('common:buttons.testModel')}
                    </button>
                  </div>
                </div>
                
                {useCustomDefaultModel ? (
                  <input
                    type="text"
                    value={formData.default_model || ''}
                    onChange={(e) => updateFormField('default_model', e.target.value)}
                    className="input w-full"
                    placeholder={t('pages:settings.api.defaultModel.placeholder')}
                  />
                ) : (
                  <select
                    value={formData.default_model || ''}
                    onChange={(e) => updateFormField('default_model', e.target.value)}
                    disabled={modelsLoadingState === 'loading'}
                    className={`input w-full ${modelsLoadingState === 'loading' ? 'bg-gray-100' : ''}`}
                  >
                    {modelsLoadingState === 'loading' ? (
                      <option value="">{t('pages:settings.api.defaultModel.loadingModels')}</option>
                    ) : availableModels?.error ? (
                      <option value="">{t('pages:settings.api.defaultModel.failedToLoad')}</option>
                    ) : (
                      availableModels?.models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.id} {model.recommended ? t('pages:settings.api.defaultModel.recommended') : ''}
                        </option>
                      ))
                    )}
                  </select>
                )}
                
                <p className="text-sm text-gray-500 mt-1">
                  {useCustomDefaultModel 
                    ? t('pages:settings.api.defaultModel.customDescription')
                    : t('pages:settings.api.defaultModel.description')
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
                    {t('pages:settings.api.translateModel.label')}
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={useCustomTranslateModel}
                      onChange={(e) => setUseCustomTranslateModel(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-600">{t('pages:settings.api.defaultModel.useCustom')}</span>
                  </label>
                </div>
                
                {useCustomTranslateModel ? (
                  <input
                    type="text"
                    value={formData.translate_model || ''}
                    onChange={(e) => updateFormField('translate_model', e.target.value)}
                    className="input w-full"
                    placeholder={t('pages:settings.api.defaultModel.placeholder')}
                  />
                ) : (
                  <select
                    value={formData.translate_model || ''}
                    onChange={(e) => updateFormField('translate_model', e.target.value)}
                    disabled={modelsLoadingState === 'loading'}
                    className={`input w-full ${modelsLoadingState === 'loading' ? 'bg-gray-100' : ''}`}
                  >
                    {modelsLoadingState === 'loading' ? (
                      <option value="">{t('pages:settings.api.defaultModel.loadingModels')}</option>
                    ) : availableModels?.error ? (
                      <option value="">{t('pages:settings.api.defaultModel.failedToLoad')}</option>
                    ) : (
                      availableModels?.models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.id} {model.recommended ? t('pages:settings.api.defaultModel.recommended') : ''}
                        </option>
                      ))
                    )}
                  </select>
                )}
                
                <p className="text-sm text-gray-500 mt-1">
                  {useCustomTranslateModel 
                    ? t('pages:settings.api.defaultModel.customDescription')
                    : t('pages:settings.api.translateModel.description')
                  }
                </p>
                {availableModels?.error && !useCustomTranslateModel && (
                  <p className="text-sm text-red-600 mt-1">
                    Error: {availableModels.error}
                  </p>
                )}
              </div>

              {/* Model Test Results */}
              {modelTestResult && (
                <div className={`border rounded-md p-4 ${
                  modelTestResult.available 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className={`font-medium ${
                    modelTestResult.available ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {t('pages:settings.api.modelTestResult')}: {modelTestResult.available ? t('common:status.available') : t('common:status.notAvailable')}
                  </div>
                  
                  {modelTestResult.available && (
                    <div className="mt-3 space-y-2">
                      <div className="text-sm">
                        <strong>{t('pages:settings.api.modelId')}:</strong> {modelTestResult.model_id}
                      </div>
                      
                      {modelTestResult.capabilities && (
                        <div className="text-sm">
                          <strong>{t('pages:settings.api.capabilities')}:</strong>
                          <div className="ml-4 mt-1 space-y-1">
                            <div className="flex items-center">
                              <span className={`w-3 h-3 rounded-full mr-2 ${
                                modelTestResult.capabilities.supports_images ? 'bg-green-500' : 'bg-gray-300'
                              }`}></span>
                              <span>{t('pages:settings.api.imageSupport')}: {modelTestResult.capabilities.supports_images ? t('common:labels.yes') : t('common:labels.no')}</span>
                            </div>
                            <div className="flex items-center">
                              <span className={`w-3 h-3 rounded-full mr-2 ${
                                modelTestResult.capabilities.supports_files ? 'bg-green-500' : 'bg-gray-300'
                              }`}></span>
                              <span>{t('pages:settings.api.fileUploadSupport')}: {modelTestResult.capabilities.supports_files ? t('common:labels.yes') : t('common:labels.no')}</span>
                            </div>
                            {modelTestResult.capabilities.context_length && (
                              <div className="text-xs text-gray-600">
                                {t('pages:settings.api.contextLength')}: {modelTestResult.capabilities.context_length.toLocaleString()} tokens
                              </div>
                            )}
                            {modelTestResult.capabilities.max_tokens && (
                              <div className="text-xs text-gray-600">
                                {t('pages:settings.api.maxOutput')}: {modelTestResult.capabilities.max_tokens.toLocaleString()} tokens
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {modelTestResult.response && (
                        <div className="text-sm">
                          <strong>{t('pages:settings.api.testResponse')}:</strong> {modelTestResult.response}
                        </div>
                      )}
                      
                      {modelTestResult.usage && (
                        <div className="text-xs text-gray-600">
                          {t('pages:settings.api.tokenUsage')}: {modelTestResult.usage.total_tokens || t('common:labels.notAvailable')} {t('common:labels.total')}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {!modelTestResult.available && modelTestResult.error && (
                    <div className="mt-2 text-sm text-red-700">
                      <strong>{t('common:labels.error')}:</strong> {modelTestResult.error}
                    </div>
                  )}
                </div>
              )}

            </div>
          )}

          {activeTab === 'processing' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">{t('pages:settings.processing.title')}</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.processing.maxPaperLength.label')}
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
                  {t('pages:settings.processing.maxPaperLength.description')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.processing.requestTimeout.label')}
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
                  {t('pages:settings.processing.requestTimeout.description')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.processing.defaultOutputFormat.label')}
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
                  {t('pages:settings.processing.defaultLanguage.label')}
                </label>
                <select
                  value={formData.default_language || ''}
                  onChange={(e) => updateFormField('default_language', e.target.value)}
                  className="input w-full"
                >
                  <option value="en">{t('common:labels.english')}</option>
                  <option value="zh">{t('common:labels.chinese')}</option>
                </select>
              </div>
            </div>
          )}

          {activeTab === 'image' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">{t('pages:settings.image.title')}</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.image.maxImageSize.label')}
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
                  {t('pages:settings.image.maxImageSize.description')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.image.imageQuality.label')}
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
                  {t('pages:settings.image.imageQuality.description')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.image.maxImageDimension.label')}
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
                  {t('pages:settings.image.maxImageDimension.description')}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">{t('pages:settings.system.title')}</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('pages:settings.system.logLevel.label')}
                </label>
                <select
                  value={formData.log_level || ''}
                  onChange={(e) => updateFormField('log_level', e.target.value)}
                  className="input w-full"
                >
                  <option value="DEBUG">{t('common:labels.debug')}</option>
                  <option value="INFO">{t('common:labels.info')}</option>
                  <option value="WARNING">{t('common:labels.warning')}</option>
                  <option value="ERROR">{t('common:labels.error')}</option>
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  {t('pages:settings.system.logLevel.description')}
                </p>
              </div>

              {config?.colors && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('pages:settings.system.colorScheme.label')}
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
                <h4 className="font-medium text-gray-900 mb-2">{t('pages:settings.system.configurationFiles.title')}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>{t('pages:settings.system.configurationFiles.envFile')}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      validation?.env_file_exists 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {validation?.env_file_exists ? t('pages:settings.system.configurationFiles.exists') : t('pages:settings.system.configurationFiles.notFound')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>{t('pages:settings.system.configurationFiles.configFile')}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      validation?.config_file_exists 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {validation?.config_file_exists ? t('pages:settings.system.configurationFiles.exists') : t('pages:settings.system.configurationFiles.notFound')}
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
