# MindMenders Mental Health Chatbot Integration

## Overview
The MindMenders/Mental_Health_Chatbot model has been added to EchoLearn's WebLLM configuration for local AI processing.

## Model Details
- **Name**: MindMenders Mental Health
- **ID**: `MindMenders-Mental-Health-Chatbot-q4f16_1-MLC`
- **Size**: 2.8GB
- **Parameters**: 7B
- **Description**: Specialized mental health support chatbot

## Important Notes

### ⚠️ **Model Conversion Required**
The original MindMenders/Mental_Health_Chatbot from Hugging Face needs to be converted to **MLC (Machine Learning Compilation)** format to work with WebLLM. 

**Current Status**: The model ID has been added to the configuration, but the actual MLC-converted model files need to be available.

### 🔧 **Model Conversion Process**
To make this model work, you need:

1. **Convert the model** using MLC-LLM tools:
   ```bash
   # Install MLC-LLM
   pip install mlc-llm
   
   # Convert the model
   mlc_llm convert_weight \
     --model-path MindMenders/Mental_Health_Chatbot \
     --quantization q4f16_1 \
     --output ./MindMenders-Mental-Health-Chatbot-q4f16_1-MLC
   ```

2. **Host the converted model** on a CDN or server accessible to WebLLM

3. **Update the model registry** in WebLLM's supported models list

### 🎯 **Integration Points**
The model has been added to:
- ✅ `webllm-service.ts` - Main service configuration
- ✅ `webllm-service-backup.ts` - Backup service configuration  
- ✅ `webllm-widget.js` - Standalone widget configuration
- ✅ `ModelSelector.tsx` - UI component for model selection

### 🚀 **Usage Instructions**
Once the MLC-converted model is available:

1. **Open Settings** in EchoLearn
2. **Navigate to Local AI Models** section
3. **Find "MindMenders Mental Health"** in the model list
4. **Click Download** to cache the model locally
5. **Select the model** when download completes
6. **Start chatting** with specialized mental health support

### 🔗 **Related Resources**
- [Original Model on Hugging Face](https://huggingface.co/MindMenders/Mental_Health_Chatbot)
- [MLC-LLM Documentation](https://mlc.ai/docs/)
- [WebLLM Supported Models](https://github.com/mlc-ai/web-llm/blob/main/src/prebuilt_models.ts)

### 📝 **Next Steps**
1. Contact the MindMenders team about MLC conversion
2. Or use MLC-LLM tools to convert the model yourself
3. Host the converted model files
4. Test the integration in EchoLearn

---
*Note: This integration assumes the model will be converted to MLC format. Without conversion, the download will fail when attempted.*