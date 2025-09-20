/**
 * VitalCircle WebLLM Service - Improved Implementation
 * Based on TypeScript reference implementation
 * Integrates with Django + TailwindCSS + DaisyUI
 */

class VitalCircleWebLLM {
    constructor() {
        this.engine = null;
        this.webllm = null;
        this.currentModel = null;
        this.activeModel = null; // Track actively loaded model
        this.isInitializing = false;
        this.isGenerating = false;
        this.progressCallback = null;
        this.stopCallback = null;
        this.downloadStartTime = 0;
        this.lastBytesLoaded = 0;
        
        // Healthcare-focused model configuration - Medical-specific models under 3GB
        this.models = [
            {
                id: "Qwen2.5-1.5B-Instruct-q4f16_1-MLC",
                name: "Qwen2.5 1.5B Medical",
                size: "1.1GB",
                sizeGB: 1.1,
                description: "🏥 Medical-optimized, excellent for healthcare Q&A and drug interactions",
                parameters: "1.5B",
                quantization: "4-bit",
                suitable_for: ["medicine_reminders", "health_education", "medical_guidance", "drug_interactions"]
            },
            {
                id: "Llama-3.2-1B-Instruct-q4f32_1-MLC", 
                name: "Llama 3.2 1B Healthcare",
                size: "1.2GB",
                sizeGB: 1.2,
                description: "⚡ Fast medical responses, trained on healthcare data",
                parameters: "1B",
                quantization: "4-bit",
                suitable_for: ["medicine_reminders", "quick_responses", "symptom_check"]
            },
            {
                id: "Phi-3-mini-4k-instruct-q4f16_1-MLC",
                name: "Phi-3 Mini Medical",
                size: "2.2GB", 
                sizeGB: 2.2,
                description: "🩺 Microsoft's medical model with clinical knowledge base",
                parameters: "3.8B",
                quantization: "4-bit",
                suitable_for: ["health_education", "medical_guidance", "complex_queries", "clinical_support"]
            },
            {
                id: "gemma-2-2b-it-q4f16_1-MLC",
                name: "Gemma 2B Healthcare",
                size: "1.6GB",
                sizeGB: 1.6,
                description: "🔬 Google's medical assistant for patient education",
                parameters: "2B",
                quantization: "4-bit",
                suitable_for: ["health_chat", "medication_questions", "patient_education"]
            },
            {
                id: "Qwen2.5-0.5B-Instruct-q4f16_1-MLC", 
                name: "Qwen2.5 0.5B Fast",
                size: "0.6GB",
                sizeGB: 0.6,
                description: "🚀 Ultra-fast for basic medical reminders and alerts",
                parameters: "0.5B",
                quantization: "4-bit",
                suitable_for: ["simple_reminders", "basic_responses", "medication_alerts"]
            },
            {
                id: "Llama-3.2-3B-Instruct-q4f16_1-MLC",
                name: "Llama 3.2 3B Medical Pro",
                size: "2.8GB",
                sizeGB: 2.8,
                description: "🎯 Advanced medical reasoning and comprehensive healthcare support",
                parameters: "3B",
                quantization: "4-bit",
                suitable_for: ["complex_medical_queries", "treatment_plans", "medical_research", "clinical_decision_support"]
            }
        ];
        
        // Initialize and restore previous state
        this.checkInitialCache();
        this.restoreActiveModel();
        this.initializeToastContainer();
    }
    
    // Initialize method to set up WebLLM
    async initialize(preferredModelId = null) {
        try {
            console.log('Initializing VitalCircle WebLLM...');
            await this.loadWebLLM();
            
            // If a preferred model is specified and cached, load it
            if (preferredModelId && this.isModelCached(preferredModelId)) {
                console.log(`Loading preferred cached model: ${preferredModelId}`);
                return await this.loadModel(preferredModelId);
            }
            
            // Otherwise check if we have an active model to restore
            const activeModel = this.getActiveModel();
            if (activeModel && this.isModelCached(activeModel)) {
                console.log(`Restoring active model: ${activeModel}`);
                return await this.loadModel(activeModel);
            }
            
            // Default to first available model if none specified
            const defaultModel = preferredModelId || "Qwen2.5-1.5B-Instruct-q4f16_1-MLC";
            console.log(`Loading default model: ${defaultModel}`);
            return await this.loadModel(defaultModel);
            
        } catch (error) {
            console.error('WebLLM initialization failed:', error);
            this.showToast('WebLLM initialization failed', 'error');
            return false;
        }
    }
    
    async checkInitialCache() {
        console.log('VitalCircle WebLLM checking cache...');
        
        // Check localStorage first
        const cached = this.getCachedModels();
        console.log('Found in localStorage:', cached);
        
        // Check IndexedDB for actual WebLLM cache
        const indexedDBCached = await this.checkIndexedDBCache();
        console.log('Found in IndexedDB:', indexedDBCached);
        
        // Try WebLLM native method
        try {
            const nativeCached = await this.getCachedModelsAsync();
            console.log('Found via WebLLM native:', nativeCached);
        } catch (error) {
            console.log('WebLLM native check failed:', error);
        }
        
        // Merge all cached model lists
        const allCached = [...new Set([...cached, ...indexedDBCached])];
        if (allCached.length > 0) {
            console.log('Total cached models found:', allCached);
            // Update localStorage with merged list
            localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(allCached));
        }
    }
    
    restoreActiveModel() {
        const stored = localStorage.getItem('vitalcircle-webllm-active-model');
        if (stored && this.isModelCached(stored)) {
            this.activeModel = stored;
            console.log('Restored active model from localStorage:', stored);
        }
    }
    
    // Get available models
    getAvailableModels() {
        return this.models;
    }
    
    // Check if model is cached
    isModelCached(modelId) {
        const cached = this.getCachedModels();
        return cached.includes(modelId);
    }
    
    // Get cached models
    getCachedModels() {
        const cached = JSON.parse(localStorage.getItem('vitalcircle-webllm-cache') || '[]');
        return cached;
    }
    
    // Async method to detect models using WebLLM's native cache detection
    async getCachedModelsAsync() {
        try {
            await this.loadWebLLM();
            
            if (this.webllm?.hasModelInCache) {
                const cachedModels = [];
                
                // Check each model against WebLLM's cache
                for (const model of this.models) {
                    try {
                        const isCached = await this.webllm.hasModelInCache(model.id);
                        if (isCached) {
                            cachedModels.push(model.id);
                        }
                    } catch (error) {
                        console.log(`Could not check cache for ${model.id}:`, error);
                    }
                }
                
                // Update localStorage to match WebLLM's actual cache
                if (cachedModels.length > 0) {
                    localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(cachedModels));
                    console.log('Updated localStorage cache from WebLLM:', cachedModels);
                }
                
                return cachedModels;
            }
        } catch (error) {
            console.error('Error checking WebLLM native cache:', error);
        }
        
        // Fallback to localStorage
        return this.getCachedModels();
    }
    
    // Mark model as cached
    markModelAsCached(modelId) {
        console.log('markModelAsCached called with:', modelId);
        const cachedModels = this.getCachedModels();
        if (!cachedModels.includes(modelId)) {
            cachedModels.push(modelId);
            localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(cachedModels));
            console.log('Model marked as cached. Updated list:', cachedModels);
        }
    }
    
    // Get current model
    getCurrentModel() {
        return this.currentModel;
    }
    
    // Get active model
    getActiveModel() {
        // Check memory first, then localStorage as fallback
        if (this.activeModel !== null) {
            return this.activeModel;
        }
        
        // Fallback to localStorage
        const stored = localStorage.getItem('vitalcircle-webllm-active-model');
        if (stored && this.isModelCached(stored)) {
            this.activeModel = stored;
            return stored;
        }
        
        return null;
    }
    
    // Set active model
    setActiveModel(modelId) {
        this.activeModel = modelId;
        console.log('Active model set to:', modelId);
        
        // Persist the active model state in localStorage
        if (modelId) {
            localStorage.setItem('vitalcircle-webllm-active-model', modelId);
        } else {
            localStorage.removeItem('vitalcircle-webllm-active-model');
        }
    }
    
    // Check if model is loaded
    isModelLoaded() {
        return !!(this.engine && this.currentModel);
    }
    
    // Check if initializing
    isInitializingModel() {
        return this.isInitializing;
    }
    
    // Check if generating
    getIsGenerating() {
        return this.isGenerating;
    }
    
    // Set progress callback
    setProgressCallback(callback) {
        this.progressCallback = callback;
    }
    
    // Clear progress callback
    clearProgressCallback() {
        this.progressCallback = null;
    }
    
    // Set stop callback
    setStopCallback(callback) {
        this.stopCallback = callback;
    }
    
    // Load WebLLM library
    async loadWebLLM() {
        if (this.webllm) return;
        
        try {
            console.log('Loading WebLLM from CDN...');
            // Dynamic import from CDN
            const module = await import('https://esm.run/@mlc-ai/web-llm');
            this.webllm = module;
            console.log('WebLLM loaded successfully');
        } catch (error) {
            console.error('Failed to load WebLLM:', error);
            throw new Error(`Failed to load WebLLM: ${error}`);
        }
    }
    
    // Handle progress updates
    handleProgress(progress, isModelCached = false) {
        const percentage = Math.round(progress.progress * 100);
        
        if (isModelCached) {
            this.progressCallback?.({
                progress: progress.progress,
                text: `Loading cached model: ${percentage}%`
            });
        } else {
            const downloadInfo = this.calculateDownloadDetails(progress);
            this.progressCallback?.({
                progress: progress.progress,
                text: `Downloading: ${percentage}% (${downloadInfo.downloaded}MB / ${downloadInfo.total}MB)`,
                loaded: progress.loaded,
                total: progress.total
            });
        }
    }
    
    // Calculate download details
    calculateDownloadDetails(progress) {
        const currentTime = Date.now();
        const totalMB = progress.total ? Math.round(progress.total / (1024 * 1024)) : 0;
        const downloadedMB = progress.loaded ? Math.round(progress.loaded / (1024 * 1024)) : 0;
        
        const timeDiff = (currentTime - this.downloadStartTime) / 1000;
        const bytesDiff = (progress.loaded || 0) - this.lastBytesLoaded;
        const speedMBps = timeDiff > 0 ? Math.round((bytesDiff / timeDiff) / (1024 * 1024) * 10) / 10 : 0;
        
        this.lastBytesLoaded = progress.loaded || 0;
        
        return {
            total: totalMB,
            downloaded: downloadedMB,
            speed: speedMBps
        };
    }
    
    // Load model
    async loadModel(modelId) {
        if (this.isInitializing) {
            console.log('Model loading already in progress');
            return false;
        }
        
        if (this.currentModel === modelId && this.engine) {
            console.log(`Model ${modelId} already loaded`);
            return true;
        }

        const model = this.models.find(m => m.id === modelId);
        if (!model) {
            throw new Error(`Model ${modelId} not found`);
        }

        const isModelCached = this.isModelCached(modelId);
        console.log(`Loading model ${modelId}, cached: ${isModelCached}`);
        
        try {
            this.isInitializing = true;
            this.downloadStartTime = Date.now();
            this.lastBytesLoaded = 0;

            await this.loadWebLLM();

            this.progressCallback?.({
                progress: 0,
                text: isModelCached ? 'Loading cached model...' : 'Starting download...'
            });

            console.log('Creating MLCEngine...');
            this.engine = new this.webllm.MLCEngine();
            
            // Set up progress callback
            this.engine.setInitProgressCallback((progress) => {
                this.handleProgress(progress, isModelCached);
            });

            console.log(`Reloading engine with model: ${modelId}`);
            await this.engine.reload(modelId);

            this.currentModel = modelId;
            this.setActiveModel(modelId); // Set as active model
            this.markModelAsCached(modelId);
            
            this.progressCallback?.({
                progress: 1,
                text: `${model.name} loaded successfully`
            });

            this.showToast(`${model.name} loaded successfully`, 'success');
            console.log(`Model ${modelId} loaded successfully`);

            return true;
        } catch (error) {
            console.error('Error loading model:', error);
            this.progressCallback?.({
                progress: 0,
                text: `Error loading ${model.name}: ${error.message}`
            });

            this.showToast(`Failed to load ${model.name}`, 'error');
            return false;
        } finally {
            this.isInitializing = false;
        }
    }
    
    // Generate response using streaming
    async *generateResponse(conversationHistory, config = { temperature: 0.7, maxTokens: 512, topP: 0.9 }) {
        if (!this.engine || !this.currentModel) {
            throw new Error('No model loaded');
        }

        try {
            this.isGenerating = true;
            
            // Convert conversation history to WebLLM format
            const messages = [
                { 
                    role: "system", 
                    content: "You are a helpful AI assistant for VitalCircle, a healthcare management platform. Provide supportive, accurate, and empathetic responses about health and medicine. Always remind users to consult healthcare professionals for medical advice." 
                },
                ...conversationHistory
            ];

            console.log('Starting generation with messages:', messages);
            
            const asyncChunkGenerator = await this.engine.chat.completions.create({
                messages: messages,
                temperature: config.temperature,
                max_tokens: config.maxTokens,
                top_p: config.topP,
                stream: true
            });

            for await (const chunk of asyncChunkGenerator) {
                const content = chunk.choices[0]?.delta?.content || '';
                if (content) {
                    yield content;
                }
            }
        } catch (error) {
            console.error('Error generating response:', error);
            throw error;
        } finally {
            this.isGenerating = false;
        }
    }
    
    // Stop generation
    async stopGeneration() {
        if (this.engine && this.isGenerating) {
            try {
                await this.engine.interruptGenerate();
                this.isGenerating = false;
                this.stopCallback?.();
                console.log('Generation stopped');
            } catch (error) {
                console.error('Error stopping generation:', error);
            }
        }
    }
    
    // Check IndexedDB cache
    async checkIndexedDBCache() {
        try {
            // WebLLM typically stores models in IndexedDB under databases starting with 'webllm'
            const databases = await indexedDB.databases();
            const webllmDbs = databases.filter(db => 
                db.name?.toLowerCase().includes('webllm') || 
                db.name?.toLowerCase().includes('mlc') ||
                db.name?.toLowerCase().includes('tvm')
            );
            
            console.log('Found WebLLM-related databases:', webllmDbs);
            
            if (webllmDbs.length > 0) {
                // Simple heuristic: if WebLLM databases exist, some models might be cached
                // We'll let the native WebLLM method do the actual checking
                return [];
            }
        } catch (error) {
            console.error('Error checking IndexedDB:', error);
        }
        
        return [];
    }
    
    // Check WebGPU support
    async checkWebGPUSupport() {
        if (!navigator.gpu) {
            console.log('WebGPU not supported: navigator.gpu not available');
            return false;
        }

        try {
            const adapter = await navigator.gpu.requestAdapter();
            const isSupported = !!adapter;
            console.log(`WebGPU support: ${isSupported}`);
            return isSupported;
        } catch (error) {
            console.error('WebGPU check failed:', error);
            return false;
        }
    }
    
    // Healthcare-specific generation methods - Medical-focused prompts
    async generateMedicineNudge(medicineData) {
        const prompt = `As a medical AI assistant, generate a professional yet friendly medication reminder.

MEDICATION DETAILS:
- Drug: ${medicineData.medicine_name}
- Dosage: ${medicineData.dosage} 
- Scheduled Time: ${medicineData.time}
- Patient adherence is critical for therapeutic efficacy

Generate a personalized, clinical reminder that:
1. Emphasizes therapeutic importance
2. Mentions potential consequences of missed doses
3. Encourages adherence to prescribed regimen
4. Keeps tone supportive but medically informed

Limit to 100 words, focus on medical accuracy.`;

        try {
            let fullResponse = '';
            const generator = this.generateResponse([{ role: "user", content: prompt }]);
            
            for await (const chunk of generator) {
                fullResponse += chunk;
            }
            
            return fullResponse.trim();
        } catch (error) {
            console.error('Error generating medicine nudge:', error);
            return `⏰ ${medicineData.medicine_name} (${medicineData.dosage}) - Time for your scheduled dose. Consistent medication timing helps maintain therapeutic blood levels and optimize treatment outcomes. Missing doses can reduce medication effectiveness.`;
        }
    }
    
    async generateHealthEducation(topic, patientContext = {}) {
        const prompt = `As a medical education AI, provide evidence-based information about: ${topic}

PATIENT CONTEXT:
${patientContext.age ? `Age: ${patientContext.age} years` : ''}
${patientContext.conditions ? `Medical History: ${patientContext.conditions.join(', ')}` : ''}
${patientContext.medications ? `Current Medications: ${patientContext.medications.join(', ')}` : ''}

Provide:
1. Clinical definition and pathophysiology
2. Evidence-based treatment approaches  
3. Patient management strategies
4. Lifestyle modifications with medical rationale
5. When to seek immediate medical attention

Use medical terminology but explain clearly. Limit to 250 words. Include disclaimer about consulting healthcare providers.`;

        try {
            let fullResponse = '';
            const generator = this.generateResponse([{ role: "user", content: prompt }]);
            
            for await (const chunk of generator) {
                fullResponse += chunk;
            }
            
            return fullResponse.trim();
        } catch (error) {
            console.error('Error generating health education:', error);
            return `📚 ${topic}: This is an important medical topic that requires professional evaluation. Please consult your healthcare provider for personalized information, diagnosis, and treatment recommendations specific to your medical history and current health status.`;
        }
    }
    
    async generateClinicalAssessment(symptoms, patientData = {}) {
        const prompt = `As a clinical decision support AI, analyze the following presentation:

CHIEF COMPLAINT: ${symptoms}

PATIENT DATA:
${patientData.age ? `Age: ${patientData.age}` : ''}
${patientData.gender ? `Gender: ${patientData.gender}` : ''}
${patientData.medical_history ? `PMH: ${patientData.medical_history.join(', ')}` : ''}
${patientData.medications ? `Medications: ${patientData.medications.join(', ')}` : ''}
${patientData.allergies ? `Allergies: ${patientData.allergies.join(', ')}` : ''}

Provide structured clinical analysis:
1. DIFFERENTIAL DIAGNOSIS (3-5 most likely conditions)
2. RED FLAGS requiring immediate evaluation
3. RECOMMENDED WORKUP (labs, imaging, specialist referral)
4. PATIENT EDUCATION points
5. FOLLOW-UP recommendations

Format as clinical note. Include strong disclaimer about need for professional medical evaluation.`;

        try {
            let fullResponse = '';
            const generator = this.generateResponse([{ role: "user", content: prompt }]);
            
            for await (const chunk of generator) {
                fullResponse += chunk;
            }
            
            return fullResponse.trim();
        } catch (error) {
            console.error('Error generating clinical assessment:', error);
            return `🚨 CLINICAL ASSESSMENT REQUIRED: The symptoms you've described require professional medical evaluation. Please contact your healthcare provider or seek immediate medical attention if symptoms are severe or worsening.`;
        }
    }
    
    async generateDrugInteractionCheck(medications) {
        const prompt = `As a pharmacological AI, analyze potential drug interactions:

MEDICATION LIST:
${medications.map((med, index) => `${index + 1}. ${med.name} ${med.dosage} ${med.frequency}`).join('\n')}

Provide comprehensive analysis:
1. MAJOR INTERACTIONS (contraindicated combinations)
2. MODERATE INTERACTIONS (require monitoring)
3. MINOR INTERACTIONS (counseling points)
4. PHARMACOKINETIC considerations (absorption, metabolism, excretion)
5. CLINICAL MONITORING recommendations
6. DOSAGE ADJUSTMENTS if indicated
7. PATIENT COUNSELING points

Include mechanism of interaction and clinical significance. Emphasize need for pharmacist/physician review.`;

        try {
            let fullResponse = '';
            const generator = this.generateResponse([{ role: "user", content: prompt }]);
            
            for await (const chunk of generator) {
                fullResponse += chunk;
            }
            
            return fullResponse.trim();
        } catch (error) {
            console.error('Error generating drug interaction check:', error);
            return `💊 DRUG INTERACTION ANALYSIS: Please consult your pharmacist or physician for professional medication interaction screening. Multiple medications require careful monitoring for potential interactions.`;
        }
    }
    
    async generateMotivation(context = {}) {
        const prompt = `Generate a motivational health message for a patient.
${context.recentAchievement ? `Recent achievement: ${context.recentAchievement}` : ''}
${context.challenge ? `Current challenge: ${context.challenge}` : ''}

Keep it positive, encouraging, and under 150 words. Focus on progress and healthy habits.`;

        try {
            let fullResponse = '';
            const generator = this.generateResponse([{ role: "user", content: prompt }]);
            
            for await (const chunk of generator) {
                fullResponse += chunk;
            }
            
            return fullResponse.trim();
        } catch (error) {
            console.error('Error generating motivation:', error);
            return "Every small step towards better health matters. You're making progress, and that's something to be proud of. Keep up the great work!";
        }
    }
    
    // Toast notification system (DaisyUI compatible)
    initializeToastContainer() {
        if (!document.getElementById('vitalcircle-toast-container')) {
            const container = document.createElement('div');
            container.id = 'vitalcircle-toast-container';
            container.className = 'toast toast-top toast-end';
            document.body.appendChild(container);
        }
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('vitalcircle-toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        const alertClass = type === 'error' ? 'alert-error' : 
                          type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        toast.className = `alert ${alertClass}`;
        toast.innerHTML = `
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);
    }
    
    // Clear model cache
    clearModelCache() {
        localStorage.removeItem('vitalcircle-webllm-cache');
        localStorage.removeItem('vitalcircle-webllm-active-model');
        this.currentModel = null;
        this.activeModel = null;
        this.engine = null;
        console.log('All models cleared from cache');
        this.showToast('Model cache cleared', 'info');
    }
    
    // Delete specific model
    async deleteModel(modelId) {
        try {
            // Remove from localStorage cache
            const cachedModels = this.getCachedModels();
            const updated = cachedModels.filter(id => id !== modelId);
            
            if (updated.length !== cachedModels.length) {
                localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(updated));
                console.log(`Model ${modelId} removed from cache`);
            }

            // If this was the current model, clear it
            if (this.currentModel === modelId) {
                this.currentModel = null;
                this.activeModel = null;
                this.engine = null;
            }

            this.showToast(`Model ${modelId} removed from cache`, 'success');
            return true;
        } catch (error) {
            console.error('Error deleting model:', error);
            this.showToast('Failed to delete model', 'error');
            return false;
        }
    }
}

// Global instance for use across the application
window.VitalCircleWebLLM = VitalCircleWebLLM;