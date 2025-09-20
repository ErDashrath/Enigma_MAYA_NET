/**
 * VitalCircle WebLLM Service - Vanilla JavaScript
 * Integrates with Django + TailwindCSS + DaisyUI
 * No React - Pure vanilla JS for medicine alerts and AI nudges
 */

class VitalCircleWebLLM {
    constructor() {
        this.engine = null;
        this.webllm = null;
        this.currentModel = null;
        this.isInitializing = false;
        this.isGenerating = false;
        this.progressCallback = null;
        this.onNudgeGenerated = null;
        
        // Healthcare-focused models for medicine alerts
        this.models = [
            {
                id: "Llama-3.2-1B-Instruct-q4f32_1-MLC",
                name: "Llama 3.2 1B",
                size: "1.2GB",
                sizeGB: 1.2,
                description: "Fast responses for medicine reminders",
                parameters: "1B",
                suitable_for: ["medicine_reminders", "quick_responses"]
            },
            {
                id: "Phi-3-mini-4k-instruct-q4f16_1-MLC", 
                name: "Phi-3 Mini",
                size: "2.2GB",
                sizeGB: 2.2,
                description: "Medical knowledge and health guidance",
                parameters: "3.8B",
                suitable_for: ["health_education", "medical_guidance"]
            },
            {
                id: "Qwen2.5-1.5B-Instruct-q4f16_1-MLC",
                name: "Qwen2.5 1.5B", 
                size: "1.1GB",
                sizeGB: 1.1,
                description: "Efficient health conversations",
                parameters: "1.5B",
                suitable_for: ["health_chat", "medication_questions"]
            }
        ];
        
        this.initializeToastContainer();
        this.restoreActiveModel();
    }
    
    // Initialize WebLLM with default model
    async initialize(preferredModelId = null) {
        try {
            this.showToast('Initializing AI assistant...', 'info');
            
            // Check if we have a cached model to restore
            let modelToLoad = preferredModelId || this.currentModel;
            
            // If no model specified, use the smallest fast model
            if (!modelToLoad) {
                modelToLoad = "Qwen2.5-1.5B-Instruct-q4f16_1-MLC"; // Smallest model
            }
            
            const success = await this.loadModel(modelToLoad);
            
            if (success) {
                this.showToast('AI assistant ready!', 'success');
                return true;
            } else {
                this.showToast('Failed to initialize AI assistant', 'error');
                return false;
            }
        } catch (error) {
            console.error('Initialization error:', error);
            this.showToast('Error initializing AI assistant', 'error');
            return false;
        }
    }

    // Initialize DaisyUI toast container
    initializeToastContainer() {
        if (!document.getElementById('webllm-toast-container')) {
            const container = document.createElement('div');
            container.id = 'webllm-toast-container';
            container.className = 'toast toast-top toast-end z-50';
            document.body.appendChild(container);
        }
    }
    
    // Show DaisyUI toast notification
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('webllm-toast-container');
        const toast = document.createElement('div');
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-error', 
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        toast.className = `alert ${alertClass} mb-2`;
        toast.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
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
    
    // Get available models
    getAvailableModels() {
        return this.models;
    }
    
    // Check if model is cached
    isModelCached(modelId) {
        const cached = JSON.parse(localStorage.getItem('vitalcircle-webllm-cache') || '[]');
        return cached.includes(modelId);
    }
    
    // Get cached models
    getCachedModels() {
        return JSON.parse(localStorage.getItem('vitalcircle-webllm-cache') || '[]');
    }
    
    // Mark model as cached
    markModelAsCached(modelId) {
        const cached = this.getCachedModels();
        if (!cached.includes(modelId)) {
            cached.push(modelId);
            localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(cached));
        }
    }
    
    // Restore active model from localStorage
    restoreActiveModel() {
        const stored = localStorage.getItem('vitalcircle-active-model');
        if (stored && this.isModelCached(stored)) {
            this.currentModel = stored;
        }
    }
    
    // Set progress callback
    setProgressCallback(callback) {
        this.progressCallback = callback;
    }
    
    // Set nudge generation callback
    setNudgeCallback(callback) {
        this.onNudgeGenerated = callback;
    }
    
    // Load WebLLM library
    async loadWebLLM() {
        if (this.webllm) return;
        
        try {
            // Dynamic import from CDN
            const module = await import('https://esm.run/@mlc-ai/web-llm');
            this.webllm = module;
            console.log('WebLLM loaded successfully');
        } catch (error) {
            throw new Error(`Failed to load WebLLM: ${error.message}`);
        }
    }
    
    // Check WebGPU support
    async checkWebGPUSupport() {
        if (!navigator.gpu) {
            return false;
        }
        
        try {
            const adapter = await navigator.gpu.requestAdapter();
            return !!adapter;
        } catch (error) {
            console.error('WebGPU check failed:', error);
            return false;
        }
    }
    
    // Load model
    async loadModel(modelId) {
        if (this.isInitializing) {
            this.showToast('Model loading already in progress', 'warning');
            return false;
        }
        
        if (this.currentModel === modelId && this.engine) {
            this.showToast('Model already loaded', 'info');
            return true;
        }
        
        const model = this.models.find(m => m.id === modelId);
        if (!model) {
            this.showToast(`Model ${modelId} not found`, 'error');
            return false;
        }
        
        // Check WebGPU support
        const hasWebGPU = await this.checkWebGPUSupport();
        if (!hasWebGPU) {
            this.showToast('WebGPU not supported. Please use a compatible browser.', 'error');
            return false;
        }
        
        const isModelCached = this.isModelCached(modelId);
        
        try {
            this.isInitializing = true;
            
            // Update progress
            this.progressCallback?.({
                progress: 0,
                text: isModelCached ? 'Loading cached model...' : 'Starting download...',
                modelName: model.name
            });
            
            await this.loadWebLLM();
            
            this.engine = new this.webllm.MLCEngine();
            this.engine.setInitProgressCallback((progress) => {
                const percentage = Math.round(progress.progress * 100);
                this.progressCallback?.({
                    progress: progress.progress,
                    text: isModelCached ? 
                        `Loading ${model.name}: ${percentage}%` : 
                        `Downloading ${model.name}: ${percentage}%`,
                    modelName: model.name,
                    percentage
                });
            });
            
            await this.engine.reload(modelId);
            
            this.currentModel = modelId;
            localStorage.setItem('vitalcircle-active-model', modelId);
            this.markModelAsCached(modelId);
            
            this.progressCallback?.({
                progress: 1,
                text: `${model.name} loaded successfully`,
                modelName: model.name,
                percentage: 100
            });
            
            this.showToast(`${model.name} is ready for medicine alerts!`, 'success');
            return true;
            
        } catch (error) {
            console.error('Error loading model:', error);
            this.showToast(`Failed to load ${model.name}`, 'error');
            return false;
        } finally {
            this.isInitializing = false;
        }
    }
    
    // Generate AI nudge for medicine intake
    async generateMedicineNudge(medicineData, patientContext = {}) {
        if (!this.engine || !this.currentModel) {
            throw new Error('No model loaded. Please load a model first.');
        }
        
        const prompt = this.buildMedicineNudgePrompt(medicineData, patientContext);
        
        try {
            this.isGenerating = true;
            
            const messages = [
                {
                    role: "system",
                    content: "You are a compassionate healthcare AI assistant helping patients with medication adherence. Generate supportive, personalized reminders that are encouraging but not pushy. Keep messages concise (2-3 sentences), friendly, and focused on the patient's wellbeing."
                },
                {
                    role: "user", 
                    content: prompt
                }
            ];
            
            let response = '';
            const asyncChunkGenerator = await this.engine.chat.completions.create({
                messages: messages,
                temperature: 0.7,
                max_tokens: 150,
                top_p: 0.9,
                stream: true
            });
            
            for await (const chunk of asyncChunkGenerator) {
                const content = chunk.choices[0]?.delta?.content || '';
                if (content) {
                    response += content;
                }
            }
            
            // Clean up response
            response = response.trim();
            if (response.length > 200) {
                response = response.substring(0, 197) + '...';
            }
            
            const nudge = {
                message: response,
                medicineId: medicineData.id,
                patientId: patientContext.patientId,
                generatedAt: new Date().toISOString(),
                modelUsed: this.currentModel
            };
            
            // Trigger callback if set
            if (this.onNudgeGenerated) {
                this.onNudgeGenerated(nudge);
            }
            
            return nudge;
            
        } catch (error) {
            console.error('Error generating nudge:', error);
            throw error;
        } finally {
            this.isGenerating = false;
        }
    }
    
    // Build prompt for medicine nudge generation
    buildMedicineNudgePrompt(medicineData, patientContext) {
        const timeOfDay = this.getTimeOfDay();
        const daysSinceLastMissed = patientContext.daysSinceLastMissed || 0;
        const adherenceRate = patientContext.adherenceRate || 100;
        
        let prompt = `Generate a personalized medicine reminder message for:\n\n`;
        prompt += `Medicine: ${medicineData.medicine_name}\n`;
        prompt += `Dosage: ${medicineData.dosage}\n`;
        prompt += `Time: ${timeOfDay}\n`;
        
        if (medicineData.instructions) {
            prompt += `Instructions: ${medicineData.instructions}\n`;
        }
        
        prompt += `\nPatient context:\n`;
        if (adherenceRate < 80) {
            prompt += `- Has been struggling with adherence (${adherenceRate}% rate)\n`;
        } else if (adherenceRate > 95) {
            prompt += `- Has excellent adherence (${adherenceRate}% rate)\n`;
        }
        
        if (daysSinceLastMissed <= 3) {
            prompt += `- Recently missed a dose (${daysSinceLastMissed} days ago)\n`;
        }
        
        if (patientContext.recentSymptoms) {
            prompt += `- Recent symptoms: ${patientContext.recentSymptoms}\n`;
        }
        
        prompt += `\nGenerate a supportive, encouraging reminder that:\n`;
        prompt += `- Is warm and understanding\n`;
        prompt += `- Mentions the specific medicine and dosage\n`;
        prompt += `- Is appropriate for the time of day\n`;
        prompt += `- Includes a gentle motivation\n`;
        prompt += `- Is 2-3 sentences maximum\n`;
        
        return prompt;
    }
    
    // Get time of day for context
    getTimeOfDay() {
        const hour = new Date().getHours();
        if (hour < 12) return 'morning';
        if (hour < 17) return 'afternoon'; 
        if (hour < 21) return 'evening';
        return 'night';
    }
    
    // Generate health education content
    async generateHealthEducation(topic, patientContext = {}) {
        if (!this.engine || !this.currentModel) {
            throw new Error('No model loaded. Please load a model first.');
        }
        
        try {
            this.isGenerating = true;
            
            const prompt = `Provide helpful, accurate health education about: ${topic}. 
            Keep it simple, actionable, and encouraging. Include practical tips the patient can follow.
            Maximum 3-4 sentences.`;
            
            const messages = [
                {
                    role: "system",
                    content: "You are a knowledgeable healthcare educator. Provide accurate, helpful health information in simple terms. Always encourage patients to consult their healthcare provider for personalized advice."
                },
                {
                    role: "user",
                    content: prompt
                }
            ];
            
            let response = '';
            const asyncChunkGenerator = await this.engine.chat.completions.create({
                messages: messages,
                temperature: 0.6,
                max_tokens: 200,
                top_p: 0.8,
                stream: true
            });
            
            for await (const chunk of asyncChunkGenerator) {
                const content = chunk.choices[0]?.delta?.content || '';
                if (content) {
                    response += content;
                }
            }
            
            return response.trim();
            
        } catch (error) {
            console.error('Error generating health education:', error);
            throw error;
        } finally {
            this.isGenerating = false;
        }
    }
    
    // Generate motivational message
    async generateMotivation(context = {}) {
        if (!this.engine || !this.currentModel) {
            throw new Error('No model loaded. Please load a model first.');
        }
        
        try {
            this.isGenerating = true;
            
            let prompt = 'Generate an encouraging, uplifting message for a patient managing their health';
            if (context.recentAchievement) {
                prompt += ` who recently ${context.recentAchievement}`;
            }
            if (context.challenge) {
                prompt += ` and is working on ${context.challenge}`;
            }
            prompt += '. Keep it positive, personal, and under 2 sentences.';
            
            const messages = [
                {
                    role: "system", 
                    content: "You are a supportive healthcare companion. Generate uplifting, encouraging messages that celebrate progress and motivate continued healthy habits."
                },
                {
                    role: "user",
                    content: prompt
                }
            ];
            
            let response = '';
            const asyncChunkGenerator = await this.engine.chat.completions.create({
                messages: messages,
                temperature: 0.8,
                max_tokens: 100,
                top_p: 0.9,
                stream: true
            });
            
            for await (const chunk of asyncChunkGenerator) {
                const content = chunk.choices[0]?.delta?.content || '';
                if (content) {
                    response += content;
                }
            }
            
            return response.trim();
            
        } catch (error) {
            console.error('Error generating motivation:', error);
            throw error;
        } finally {
            this.isGenerating = false;
        }
    }
    
    // Check if currently generating
    isCurrentlyGenerating() {
        return this.isGenerating;
    }
    
    // Get current model info
    getCurrentModel() {
        return this.currentModel;
    }
    
    // Check if model is loaded
    isModelLoaded() {
        return !!(this.engine && this.currentModel);
    }
    
    // Stop current generation
    async stopGeneration() {
        if (this.engine && this.isGenerating) {
            try {
                await this.engine.interruptGenerate();
                this.isGenerating = false;
                this.showToast('Generation stopped', 'info');
            } catch (error) {
                console.error('Error stopping generation:', error);
            }
        }
    }
    
    // Delete model from cache
    async deleteModel(modelId) {
        try {
            const cached = this.getCachedModels();
            const updated = cached.filter(id => id !== modelId);
            localStorage.setItem('vitalcircle-webllm-cache', JSON.stringify(updated));
            
            if (this.currentModel === modelId) {
                this.currentModel = null;
                this.engine = null;
                localStorage.removeItem('vitalcircle-active-model');
            }
            
            this.showToast('Model removed from cache', 'success');
            return true;
        } catch (error) {
            console.error('Error deleting model:', error);
            this.showToast('Failed to delete model', 'error');
            return false;
        }
    }
    
    // Clear all models from cache
    clearAllModels() {
        localStorage.removeItem('vitalcircle-webllm-cache');
        localStorage.removeItem('vitalcircle-active-model');
        this.currentModel = null;
        this.engine = null;
        this.showToast('All models cleared from cache', 'info');
    }
}

// Global instance
window.vitalWebLLM = new VitalCircleWebLLM();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VitalCircleWebLLM;
}