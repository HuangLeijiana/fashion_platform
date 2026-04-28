const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3001;

// 中间件
app.use(cors());
app.use(express.json());

// 提供静态文件服务 - 更健壮的路径处理
app.use(express.static(path.join(__dirname)));
app.use('/static', express.static(path.join(__dirname, 'static')));

// 检查静态文件是否存在
const staticHtmlPath = path.join(__dirname, 'static', 'fashion_advisor.html');
if (!fs.existsSync(staticHtmlPath)) {
    console.log('⚠️  静态HTML文件不存在，创建基础页面...');
    createBasicHtmlFile();
}

function createBasicHtmlFile() {
    const basicHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI时尚顾问</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #007bff; color: white; margin-left: 20%; }
        .ai-message { background: #f8f9fa; margin-right: 20%; }
        input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .model-info { margin-top: 10px; font-size: 12px; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>🤖 AI时尚顾问</h1>
        <div class="messages" id="messages"></div>
        <div>
            <input type="text" id="messageInput" placeholder="输入您的时尚问题..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">发送</button>
            <button onclick="resetConversation()" style="background: #6c757d;">重置对话</button>
        </div>
        <div class="model-info">
            <span id="currentModel">模型加载中...</span>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;

            addMessage('user', message);
            input.value = '';

            // 显示加载状态
            const loadingId = addMessage('ai', '🤔 AI正在思考中，请稍候...');

            try {
                const response = await fetch('/api/fashion-advice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                if (!response.ok) throw new Error('网络请求失败');

                const data = await response.json();
                removeMessage(loadingId);
                
                if (data.error) {
                    addMessage('ai', '❌ ' + data.error);
                } else {
                    addMessage('ai', data.response);
                }
            } catch (error) {
                removeMessage(loadingId);
                addMessage('ai', '❌ 请求失败，请检查网络连接');
            }
        }

        async function resetConversation() {
            try {
                await fetch('/api/reset-conversation', { method: 'POST' });
                document.getElementById('messages').innerHTML = '';
                addMessage('ai', '🔄 对话已重置！');
            } catch (error) {
                alert('重置失败: ' + error.message);
            }
        }

        function addMessage(role, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg-' + Date.now();
            messageDiv.id = messageId;
            messageDiv.className = \`message \${role}-message\`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return messageId;
        }

        function removeMessage(messageId) {
            const element = document.getElementById(messageId);
            if (element) element.remove();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') sendMessage();
        }

        // 加载模型信息
        async function loadModelInfo() {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                document.getElementById('currentModel').textContent = \`当前模型: \${data.currentModel} | 状态: \${data.ollama}\`;
            } catch (error) {
                document.getElementById('currentModel').textContent = '模型信息加载失败';
            }
        }

        // 初始化
        window.onload = function() {
            addMessage('ai', '👋 你好！我是AI时尚顾问，可以为你提供个性化的穿搭建议。请问你有什么时尚方面的问题吗？');
            loadModelInfo();
        }
    </script>
</body>
</html>`;

    const staticDir = path.join(__dirname, 'static');
    if (!fs.existsSync(staticDir)) {
        fs.mkdirSync(staticDir, { recursive: true });
    }
    fs.writeFileSync(staticHtmlPath, basicHtml);
    console.log('✅ 已创建基础HTML文件');
}

// 添加路由直接访问时尚顾问页面
app.get('/', (req, res) => {
    if (fs.existsSync(staticHtmlPath)) {
        res.sendFile(staticHtmlPath);
    } else {
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI时尚顾问</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
                </style>
            </head>
            <body>
                <h1>🤖 AI时尚顾问</h1>
                <p>请访问 <a href="http://localhost:5000/fashion-advisor">完整版本</a></p>
            </body>
            </html>
        `);
    }
});

app.get('/fashion-advisor', (req, res) => {
    if (fs.existsSync(staticHtmlPath)) {
        res.sendFile(staticHtmlPath);
    } else {
        res.status(404).json({ error: 'HTML file not found' });
    }
});

// 检查Ollama是否可用
let ollama;
let currentModel = process.env.OLLAMA_MODEL || 'llama3.2:1b';

try {
    const { Ollama } = require('ollama');
    ollama = new Ollama({ host: 'http://localhost:11434' });
    console.log('✅ Ollama module loaded successfully');
} catch (error) {
    console.log('❌ Ollama module not available, using mock responses');
    ollama = null;
}

// 存储对话历史
let conversationHistory = [];

// 为llama3.2:1b优化的系统提示词
const systemPrompt = `你是一个时尚助手。根据用户问题提供简单实用的穿搭建议。

回答要：
- 简洁明了
- 包含具体单品
- 提到颜色搭配
- 适合场合季节

用自然的中文回答，不要太长。`;

// 针对不同模型的优化参数
function getModelOptions(modelName) {
    const baseOptions = {
        temperature: 0.7,
        top_p: 0.9,
        stream: false
    };

    if (modelName.includes('1b') || modelName.includes('0.5b')) {
        // 小模型参数 - 更保守的设置
        return {
            ...baseOptions,
            num_predict: 200,      // 减少生成长度
            top_k: 20,             // 减少词汇选择
            repeat_penalty: 1.1,
            temperature: 0.6       // 降低创造性，提高稳定性
        };
    } else {
        // 默认参数
        return {
            ...baseOptions,
            num_predict: 300,
            top_k: 40,
            repeat_penalty: 1.1
        };
    }
}

// 智能模拟回复函数
function getMockResponse(message) {
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('商务') || lowerMessage.includes('会议') || lowerMessage.includes('正式') || lowerMessage.includes('工作')) {
        return "👔 商务会议穿搭建议：\n• 上装：合身衬衫\n• 下装：深色西装裤\n• 鞋子：皮质皮鞋\n• 颜色：深蓝、灰色\n• 配饰：简约手表\n专业得体，展现自信！";
    }
    else if (lowerMessage.includes('天气') || lowerMessage.includes('晴朗') || lowerMessage.includes('阳光') || lowerMessage.includes('不错')) {
        return "☀️ 晴天穿搭推荐：\n• 上装：轻薄T恤\n• 下装：休闲裤\n• 鞋子：休闲鞋\n• 颜色：浅色系\n• 配饰：太阳镜\n舒适透气，享受好天气！";
    }
    else if (lowerMessage.includes('周末') || lowerMessage.includes('出游') || lowerMessage.includes('休闲')) {
        return "🎒 周末出游建议：\n• 上装：舒适卫衣\n• 下装：运动裤\n• 鞋子：运动鞋\n• 颜色：亮色系\n轻松舒适，活动自如！";
    }
    else if (lowerMessage.includes('约会') || lowerMessage.includes('浪漫') || lowerMessage.includes('晚餐')) {
        return "💕 约会穿搭：\n• 上装：优雅衬衫\n• 下装：修身裤装\n• 鞋子：时尚皮鞋\n• 颜色：柔和色调\n展现好气质，留下好印象！";
    }
    else if (lowerMessage.includes('夏季') || lowerMessage.includes('夏天') || lowerMessage.includes('热')) {
        return "🏖️ 夏季穿搭：\n• 上装：透气棉T\n• 下装：短裤\n• 鞋子：凉鞋\n• 颜色：清爽色系\n清凉舒适，应对炎热！";
    }
    else if (lowerMessage.includes('冬季') || lowerMessage.includes('冬天') || lowerMessage.includes('冷')) {
        return "🧣 冬季保暖穿搭：\n• 外套：羽绒服\n• 内搭：保暖毛衣\n• 下装：加厚裤装\n• 鞋子：保暖靴子\n温暖又时尚，不怕寒冷！";
    }
    else if (lowerMessage.includes('春季') || lowerMessage.includes('春天')) {
        return "🌸 春季穿搭：\n• 上装：轻薄外套\n• 内搭：长袖T恤\n• 下装：休闲裤\n• 颜色：明亮色系\n轻便舒适，适合多变天气！";
    }
    else if (lowerMessage.includes('秋季') || lowerMessage.includes('秋天')) {
        return "🍂 秋季穿搭：\n• 上装：针织衫\n• 下装：牛仔裤\n• 鞋子：休闲鞋\n• 颜色：暖色调\n温暖舒适，时尚百搭！";
    }
    else {
        return "我理解您的需求。建议选择简约款式，搭配中性色调，既时尚又得体。请告诉我更多细节，如场合、季节或偏好，我可以提供更具体的建议！";
    }
}

// 根据模型能力调整历史记录长度
function getMaxHistoryLength() {
    if (currentModel.includes('0.5b') || currentModel.includes('1b')) {
        return 4; // 小模型，减少历史记录
    } else {
        return 6; // 中等模型
    }
}

// API端点：获取时尚建议
app.post('/api/fashion-advice', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: '消息不能为空' });
        }

        console.log('📨 收到消息:', message);

        // 将用户消息添加到对话历史
        conversationHistory.push({ role: 'user', content: message });

        let aiResponse;
        let responseSource = 'mock';
        let processingTime = Date.now();

        if (ollama) {
            try {
                // 构建完整的对话上下文
                const messages = [
                    { role: 'system', content: systemPrompt },
                    ...conversationHistory.slice(-getMaxHistoryLength()) // 只保留最近的历史
                ];

                console.log(`🤖 调用Ollama模型: ${currentModel}`);

                const options = getModelOptions(currentModel);

                // 调用Ollama API
                const response = await ollama.chat({
                    model: currentModel,
                    messages: messages,
                    ...options
                });

                processingTime = Date.now() - processingTime;
                console.log(`✅ Ollama响应接收，处理时间: ${processingTime}ms`);

                aiResponse = response.message.content;
                console.log(`✨ AI响应长度: ${aiResponse.length}`);

                // 检查响应是否有效
                if (aiResponse && aiResponse.trim().length > 5) { // 降低长度要求
                    responseSource = 'ollama';
                    console.log('✅ 使用Ollama响应');
                } else {
                    console.log('⚠️  Ollama返回空或过短响应，使用模拟回复');
                    aiResponse = getMockResponse(message);
                }

            } catch (ollamaError) {
                processingTime = Date.now() - processingTime;
                console.error(`❌ Ollama API错误 (${processingTime}ms):`, ollamaError.message);
                aiResponse = getMockResponse(message);
                console.log('🔄 因Ollama错误使用模拟回复');
            }
        } else {
            aiResponse = getMockResponse(message);
            console.log('🔧 使用模拟回复 (Ollama不可用)');
        }

        // 最终检查确保响应不为空
        if (!aiResponse || aiResponse.trim() === '') {
            aiResponse = "抱歉，我暂时无法生成建议。请尝试重新提问或稍后再试。";
        }

        // 将AI回复添加到对话历史
        conversationHistory.push({
            role: 'assistant',
            content: aiResponse,
            source: responseSource
        });

        // 限制对话历史长度
        const maxHistory = getMaxHistoryLength() * 2; // 用户和AI消息各一半
        if (conversationHistory.length > maxHistory) {
            conversationHistory = conversationHistory.slice(-maxHistory);
        }

        console.log('📤 发送响应给客户端');
        res.json({
            response: aiResponse,
            source: responseSource,
            processingTime: processingTime
        });

    } catch (error) {
        console.error('💥 时尚建议端点错误:', error);
        res.status(500).json({
            error: '获取时尚建议失败',
            response: '抱歉，服务暂时不可用，请稍后重试。'
        });
    }
});

// API端点：重置对话
app.post('/api/reset-conversation', (req, res) => {
    conversationHistory = [];
    console.log('🔄 对话历史已重置');
    res.json({ message: '对话已重置成功' });
});

// API端点：获取对话历史（用于调试）
app.get('/api/conversation-history', (req, res) => {
    res.json({
        history: conversationHistory,
        length: conversationHistory.length,
        maxHistory: getMaxHistoryLength()
    });
});

// API端点：切换模型
app.post('/api/switch-model', async (req, res) => {
    const { model } = req.body;

    if (!model) {
        return res.status(400).json({ error: '模型名称不能为空' });
    }

    if (ollama) {
        try {
            // 检查模型是否存在
            const models = await ollama.list();
            const modelExists = models.models.some(m => m.name === model);

            if (modelExists) {
                currentModel = model;
                console.log(`🔄 切换到模型: ${model}`);
                res.json({
                    message: `模型切换成功`,
                    currentModel: currentModel
                });
            } else {
                res.status(404).json({
                    error: `模型 ${model} 不存在`
                });
            }
        } catch (error) {
            res.status(500).json({
                error: '检查模型时出错'
            });
        }
    } else {
        res.status(400).json({
            error: 'Ollama不可用'
        });
    }
});

// 健康检查端点
app.get('/api/health', async (req, res) => {
    let ollamaStatus = 'unavailable';
    let availableModels = [];
    let modelPerformance = {};

    if (ollama) {
        try {
            const models = await ollama.list();
            availableModels = models.models.map(m => m.name);
            ollamaStatus = 'available';

            // 模型性能信息
            modelPerformance = {
                currentModel: currentModel,
                modelSize: getModelSize(currentModel),
                recommended: isModelRecommended(currentModel),
                maxHistory: getMaxHistoryLength()
            };

        } catch (error) {
            ollamaStatus = 'error';
            console.error('健康检查错误:', error);
        }
    }

    res.json({
        status: 'OK',
        ollama: ollamaStatus,
        ...modelPerformance,
        availableModels: availableModels,
        conversationHistoryLength: conversationHistory.length,
        timestamp: new Date().toISOString()
    });
});

// 辅助函数
function getModelSize(modelName) {
    if (modelName.includes('0.5b')) return '很小';
    if (modelName.includes('1b')) return '小';
    if (modelName.includes('3b') || modelName.includes('3.8b')) return '中等';
    if (modelName.includes('7b') || modelName.includes('8b')) return '大';
    return '未知';
}

function isModelRecommended(modelName) {
    const recommendedModels = ['llama3.2:1b', 'llama3.2:3b', 'qwen2.5:0.5b', 'phi3:mini'];
    return recommendedModels.includes(modelName);
}

// 错误处理中间件
app.use((error, req, res, next) => {
    console.error('🚨 未处理的错误:', error);
    res.status(500).json({
        error: '服务器内部错误',
        message: '服务暂时不可用，请稍后重试'
    });
});

// 404处理
app.use((req, res) => {
    res.status(404).json({
        error: '接口不存在',
        message: '请求的接口未找到'
    });
});

// 启动服务器
app.listen(port, '0.0.0.0', () => {
    console.log(`=========================================`);
    console.log(`🚀 AI时尚顾问服务器已启动`);
    console.log(`📍 访问地址: http://localhost:${port}`);
    console.log(`📍 网络地址: http://127.0.0.1:${port}`);
    console.log(`🤖 使用模型: ${currentModel}`);
    console.log(`📊 模型大小: ${getModelSize(currentModel)}`);
    console.log(`⭐ 推荐度: ${isModelRecommended(currentModel) ? '推荐' : '测试中'}`);
    console.log(`⏰ 启动时间: ${new Date().toLocaleString()}`);
    console.log(`=========================================`);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('\n🛑 正在关闭服务器...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 收到终止信号，正在关闭服务器...');
    process.exit(0);
});