document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const extractBtn = document.getElementById('extract-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadingText = document.getElementById('loading-text');
    const resultsSection = document.getElementById('results-section');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const extractedTextArea = document.getElementById('extracted-text-area');
    const summaryContent = document.getElementById('summary-content');
    const generateQuizBtn = document.getElementById('generate-quiz-btn');
    const quizLoading = document.getElementById('quiz-loading');
    const quizContentContainer = document.getElementById('quiz-content-container');
    const quizContent = document.getElementById('quiz-content');

    const aiProviderSelect = document.getElementById('ai-provider');

    let currentExtractedText = '';
    let currentSummary = '';

    // 데모 모드 알림 삭제 완료
    // showToast('서버 통신 오류 방지를 위해 현재 데모 모드(Simulated Mode)로 작동 중입니다.', false);

    // TODO: REPLACE THIS URL WITH YOUR ACTUAL CLOUDFLARE WORKER URL ONCE DEPLOYED
    const WORKER_URL = 'https://flat-snowflake-43c5.rlcnfql.workers.dev';


    // Event: File Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileName.textContent = e.target.files[0].name;
            extractBtn.disabled = false;
        } else {
            fileName.textContent = '선택된 파일 없음';
            extractBtn.disabled = true;
        }
    });

    // Event: Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    // Event: Extract & Summarize
    extractBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        extractBtn.disabled = true;
        resultsSection.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');

        try {
            loadingText.textContent = '웹 브라우저에서 텍스트 또는 오디오를 추출하는 중...';
            currentExtractedText = await extractText(file);
            extractedTextArea.value = currentExtractedText;

            loadingText.textContent = 'AI 요약본을 생성하는 중...';
            currentSummary = await generateSummary(currentExtractedText);
            summaryContent.innerHTML = marked.parse(currentSummary);

            resultsSection.classList.remove('hidden');
            showToast('처리가 완료되었습니다!');
        } catch (error) {
            console.error(error);
            showToast(error.message || '처리 중 오류가 발생했습니다.', true);
        } finally {
            extractBtn.disabled = false;
            loadingIndicator.classList.add('hidden');
        }
    });

    // Event: Generate Quiz
    generateQuizBtn.addEventListener('click', async () => {
        if (!currentSummary) {
            showToast('먼저 텍스트를 추출하고 요약해주세요.', true);
            return;
        }

        const quizType = document.querySelector('input[name="quiz-type"]:checked').value;

        generateQuizBtn.disabled = true;
        quizContentContainer.classList.add('hidden');
        quizLoading.classList.remove('hidden');

        try {
            const quizHTML = await generateQuiz(currentSummary, quizType);
            // Replace markdown parsing with direct HTML injection for interactive elements
            quizContent.innerHTML = quizHTML;
            quizContentContainer.classList.remove('hidden');
            setupQuizInteractivity(quizType);
            showToast('퀴즈가 성공적으로 생성되었습니다!');
        } catch (error) {
            console.error(error);
            showToast(error.message || '퀴즈 생성 중 오류가 발생했습니다.', true);
        } finally {
            generateQuizBtn.disabled = false;
            quizLoading.classList.add('hidden');
        }
    });

    // Quiz Interactivity Logic
    function setupQuizInteractivity(quizType) {
        if (quizType.includes('객관식') || quizType.includes('O/X')) {
            const options = document.querySelectorAll('.quiz-option');
            const checkBtn = document.getElementById('check-answers-btn');
            
            options.forEach(opt => {
                opt.addEventListener('click', function() {
                    const qId = this.dataset.question;
                    // Remove selected from others in same question
                    document.querySelectorAll(`.quiz-option[data-question="${qId}"]`).forEach(o => o.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });

            if (checkBtn) {
                checkBtn.addEventListener('click', () => {
                    let allCorrect = true;
                    document.querySelectorAll('.quiz-question').forEach(q => {
                        const qId = q.dataset.id;
                        const selected = q.querySelector('.quiz-option.selected');
                        const correctVal = q.dataset.answer;
                        const explanation = q.querySelector('.explanation');
                        
                        if (selected) {
                            if (selected.dataset.value === correctVal) {
                                selected.classList.add('correct');
                            } else {
                                selected.classList.add('wrong');
                                // Highlight correct one
                                q.querySelector(`.quiz-option[data-value="${correctVal}"]`).classList.add('correct');
                                allCorrect = false;
                            }
                        } else {
                            allCorrect = false;
                        }
                        explanation.classList.remove('hidden');
                    });
                    
                    if (allCorrect) showToast('모든 정답을 맞추셨습니다! 🎉');
                    else showToast('틀린 문제가 있습니다. 해설을 확인해 보세요.', true);
                    
                    checkBtn.disabled = true;
                });
            }
        } else if (quizType.includes('주관식')) {
            const checkBtn = document.getElementById('check-answers-btn');
            if (checkBtn) {
                checkBtn.addEventListener('click', () => {
                    let allCorrect = true;
                    document.querySelectorAll('.quiz-question').forEach(q => {
                        const input = q.querySelector('input[type="text"]');
                        const correctVal = q.dataset.answer;
                        const explanation = q.querySelector('.explanation');
                        
                        // Simple similarity check for Subjective
                        if (input && input.value.trim().length > 0) {
                            if (correctVal.includes(input.value.trim()) || input.value.trim().includes(correctVal.split(' ')[0])) {
                                input.classList.add('correct-input');
                            } else {
                                input.classList.add('wrong-input');
                                allCorrect = false;
                            }
                        } else {
                            input.classList.add('wrong-input');
                            allCorrect = false;
                        }
                        explanation.classList.remove('hidden');
                    });
                    
                    if (allCorrect) showToast('훌륭합니다! 핵심 키워드를 잘 맞추셨네요! 🎉');
                    else showToast('해설을 확인하여 정답을 알아보세요.', true);
                    
                    checkBtn.disabled = true;
                });
            }
        }
    }

    // Function: Extraction Router
    async function extractText(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext === 'pdf') {
            return await extractTextFromPDF(file);
        } else if (['mp3', 'wav', 'm4a'].includes(ext)) {
            return await extractTextFromAudio(file);
        } else {
            throw new Error('지원하지 않는 파일 형식입니다.');
        }
    }

    // Function: PDF Extraction (Browser-side using PDF.js)
    async function extractTextFromPDF(file) {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let text = "";
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => item.str).join(' ');
            text += pageText + "\n";
        }
        if (!text.trim()) {
            throw new Error('PDF에서 텍스트를 추출하지 못했습니다. 스캔된 이미지 형태일 수 있습니다.');
        }
        return text;
    }

    // Function: Audio Extraction (Native Browser Speech Recognition - Note: Requires playing audio)
    // For a truly serverless free app without backend, audio transcription of files is very difficult.
    // We will simulate it or suggest the user uses a free API endpoint if we had one.
    // Here we will use a fallback message as true offline STT for files is not native to JS without large libraries.
    async function extractTextFromAudio(file) {
        return new Promise((resolve) => {
            resolve("[오디오 파일 감지됨]\n\n주의: 현재 버전은 무료/브라우저 전용 버전으로, 오디오 파일의 자동 텍스트 변환(STT) 기능이 제한적입니다. 이 기능을 완벽히 사용하려면 서버(Python 등)가 필요합니다. PDF 파일을 대신 업로드해주세요.");
        });
    }

    async function generateSummary(text) {
        const apiKey = document.getElementById('api-key-input').value.trim();
        const provider = document.getElementById('ai-provider').value;

        if (!apiKey) {
            throw new Error('API 키가 상단 우측에 필요합니다!');
        }

        const prompt = "You are a helpful study assistant. Summarize the following text into 5-10 key bullet points. Please respond in Korean if the text is in Korean.\n\n" + text;

        if (provider === 'gemini') {
            const modelsToTry = ['gemini-3-flash-preview', 'gemini-2.5-flash', 'gemini-3-pro-preview', 'gemini-2.0-flash'];
            let lastErrorData = null;

            for (const modelName of modelsToTry) {
                const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
                });

                if (response.ok) {
                    const data = await response.json();
                    return data.candidates[0].content.parts[0].text;
                } else {
                    lastErrorData = await response.json();
                    // 만약 API 키 오류라면 모델 문제가 아니므로 바로 중단합니다.
                    if (lastErrorData.error?.message?.includes("API key not valid")) {
                        throw new Error('API 키가 유효하지 않습니다. 다시 확인해주세요.');
                    }
                }
            }
            throw new Error(lastErrorData?.error?.message || 'Gemini API 모델 호출 전체 실패');

        } else if (provider === 'openai') {
            const url = `https://api.openai.com/v1/chat/completions`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'gpt-4o-mini',
                    messages: [
                        { role: 'system', content: 'You are a helpful study assistant.' },
                        { role: 'user', content: prompt }
                    ]
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'OpenAI API 호출 실패');
            }
            const data = await response.json();
            return data.choices[0].message.content;
        }
    }

    async function generateQuiz(summary, quizType) {
        const apiKey = document.getElementById('api-key-input').value.trim();
        const provider = document.getElementById('ai-provider').value;

        if (!apiKey) {
            throw new Error('API 키가 필요합니다!');
        }

        const prompt = `Based on the following summary, generate exactly 2 quiz questions of type: ${quizType}.
Format it EXACTLY in the HTML structure expected. Make sure the output is in Korean. Return ONLY the HTML code without markdown code blocks. DO NOT wrap with \`\`\`html.

If type is 객관식 (Multiple Choice):
<div class="interactive-quiz">
    <div class="quiz-question" data-id="1" data-answer="1">
        <h4>Q1. Question text</h4>
        <div class="options-grid">
            <div class="quiz-option" data-question="1" data-value="1">1. Opt 1</div>
            <div class="quiz-option" data-question="1" data-value="2">2. Opt 2</div>
            <div class="quiz-option" data-question="1" data-value="3">3. Opt 3</div>
            <div class="quiz-option" data-question="1" data-value="4">4. Opt 4</div>
        </div>
        <div class="explanation hidden mt-2 p-3 bg-opacity-20 bg-primary rounded">
            <strong>해설:</strong> explanation text
        </div>
    </div>
    <!-- Add more question blocks -->
    <button id="check-answers-btn" class="mt-4">정답 확인하기</button>
</div>

If type is 주관식 단답형 (Short Answer):
<div class="interactive-quiz">
    <div class="quiz-question" data-id="1" data-answer="정답키워드">
        <h4>Q1. Question text</h4>
        <input type="text" class="quiz-input mt-2" placeholder="정답을 입력하세요">
        <div class="explanation hidden mt-2 p-3 bg-opacity-20 bg-primary rounded">
            <strong>정답/해설:</strong> explanation text
        </div>
    </div>
    <button id="check-answers-btn" class="mt-4">정답 확인하기</button>
</div>

If type is O/X 맞추기 (True / False):
<div class="interactive-quiz">
    <div class="quiz-question" data-id="1" data-answer="O">
        <h4>Q1. Question text</h4>
        <div class="options-grid flex-row">
            <div class="quiz-option ox-option" data-question="1" data-value="O">O (그렇다)</div>
            <div class="quiz-option ox-option" data-question="1" data-value="X">X (아니다)</div>
        </div>
        <div class="explanation hidden mt-2 p-3 bg-opacity-20 bg-primary rounded">
            <strong>해설:</strong> explanation text
        </div>
    </div>
    <button id="check-answers-btn" class="mt-4">정답 확인하기</button>
</div>

Follow the exact same logic. Make sure to generate 2 questions!
Summary:
${summary}`;

        let quizHTMLText = "";

        if (provider === 'gemini') {
            const modelsToTry = ['gemini-3-flash-preview', 'gemini-2.5-flash', 'gemini-3-pro-preview', 'gemini-2.0-flash'];
            let lastErrorData = null;

            for (const modelName of modelsToTry) {
                const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
                });

                if (response.ok) {
                    const data = await response.json();
                    quizHTMLText = data.candidates[0].content.parts[0].text;
                    break;
                } else {
                    lastErrorData = await response.json();
                    if (lastErrorData.error?.message?.includes("API key not valid")) {
                        throw new Error('API 키가 유효하지 않습니다. 다시 확인해주세요.');
                    }
                }
            }
            
            if (!quizHTMLText) {
                throw new Error(lastErrorData?.error?.message || 'Gemini API 모델 호출 전체 실패');
            }
            
        } else if (provider === 'openai') {
            const url = `https://api.openai.com/v1/chat/completions`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'gpt-4o-mini',
                    messages: [
                        { role: 'system', content: 'You are a quiz generation assistant that responds ONLY with valid HTML.' },
                        { role: 'user', content: prompt }
                    ]
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'OpenAI API 호출 실패');
            }
            const data = await response.json();
            quizHTMLText = data.choices[0].message.content;
        }

        // 마크다운 코드 블록 제거(안전장치)
        quizHTMLText = quizHTMLText.replace(/^```[a-z]*\n/i, '').replace(/\n```$/i, '').trim();
        return quizHTMLText;
    }

    // Function: Toast Notification
    function showToast(message, isError = false) {
        let toast = document.getElementById('toast');
        toast.textContent = message;
        toast.style.backgroundColor = isError ? '#ef4444' : '#10b981';
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
});
