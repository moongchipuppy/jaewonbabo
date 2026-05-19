import streamlit as st
import PyPDF2
from openai import OpenAI
import os
import tempfile

# Initialize Streamlit Page
st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")

st.title("📚 AI Study Assistant")
st.write("Upload a PDF or an audio file to get a summary and generate quizzes!")

# Sidebar for API Key
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("Please enter your OpenAI API key to continue.")

    st.markdown("---")
    st.header("기능 선택")
    show_word_memo = st.button("📖 단어 암기 기능")

# 단어 암기 기능 버튼이 눌렸을 때의 동작
if show_word_memo:
    import streamlit.components.v1 as components
    
    st.header("📖 단어 암기")
    
    # 사용자가 제공한 CSS와 이에 맞는 HTML, JS를 결합한 웹앱
    vocab_html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <style>
        /* 사용자 제공 CSS */
        :root {
            --bg-color: rgba(18, 18, 18, 0.6);
            --card-bg: rgba(30, 30, 30, 0.65);
            --text-main: #e0e0e0;
            --text-muted: #aaaaaa;
            --primary: #bb86fc;
            --primary-hover: #9965f4;
            --accent: #03dac6;
            --accent-hover: #01b4a4;
            --danger: #cf6679;
            --success: #03dac6;
            --border: rgba(255, 255, 255, 0.12);
            --radius: 12px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Pretendard', sans-serif;
            background: linear-gradient(135deg, #a1c4fd 0%, #fbc2eb 100%);
            background-attachment: fixed;
            color: var(--text-main);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            justify-content: center;
        }

        .app-container {
            width: 100%;
            max-width: 800px;
            padding: 2rem 1rem;
        }

        header {
            text-align: center;
            margin-bottom: 2rem;
            animation: fadeInDown 0.5s ease;
        }

        header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #1e3a8a, #581c87);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));
        }

        header p {
            color: #334155;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            animation: fadeIn 0.5s ease;
        }

        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1.25rem;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .input-group {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }

        @media (max-width: 600px) {
            .input-group { flex-direction: column; align-items: stretch; }
        }

        .input-wrapper {
            flex: 1; display: flex; flex-direction: column; gap: 0.5rem;
        }

        .input-wrapper label { font-size: 0.9rem; color: var(--text-muted); font-weight: 600; }

        input[type="text"] {
            width: 100%; background: var(--bg-color); border: 1px solid var(--border);
            color: var(--text-main); padding: 0.75rem 1rem; border-radius: 8px; font-size: 1rem;
            transition: all 0.3s ease;
        }

        input[type="text"]:focus {
            outline: none; border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(187, 134, 252, 0.3);
        }

        .btn {
            border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 1rem;
            font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: inline-flex;
            align-items: center; justify-content: center; gap: 0.5rem;
        }

        .primary-btn { background: var(--primary); color: white; }
        .primary-btn:hover { background: var(--primary-hover); transform: translateY(-2px); }

        .accent-btn { background: var(--accent); color: white; width: 100%; padding: 1rem; font-size: 1.1rem; }
        .accent-btn:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-2px); }
        .accent-btn:disabled { background: var(--border); color: var(--text-muted); cursor: not-allowed; transform: none; }

        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .word-count { background: var(--bg-color); padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; color: var(--text-muted); border: 1px solid var(--border); }
        .word-list-container { max-height: 300px; overflow-y: auto; padding-right: 0.5rem; }
        .word-list-container::-webkit-scrollbar { width: 6px; }
        .word-list-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

        #word-list { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
        .word-item { display: flex; justify-content: space-between; align-items: center; background: var(--bg-color); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); transition: transform 0.2s; }
        .word-item:hover { transform: translateX(4px); border-color: var(--primary); }
        .word-pair { display: flex; gap: 1.5rem; }
        .word-en { font-weight: 700; color: var(--primary); width: 120px; }
        .word-ko { color: var(--text-main); }
        .delete-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 0.5rem; transition: color 0.2s; }
        .delete-btn:hover { color: var(--danger); }
        .empty-state { text-align: center; padding: 3rem 1rem; color: var(--text-muted); }

        .test-options { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        @media (max-width: 600px) { .test-options { flex-direction: column; } }
        .radio-group { flex: 1; }
        .radio-group input[type="radio"] { display: none; }
        .radio-group label { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 1rem; background: var(--bg-color); border: 2px solid var(--border); border-radius: 8px; cursor: pointer; transition: all 0.3s ease; font-weight: 600; color: var(--text-muted); }
        .radio-group input[type="radio"]:checked + label { border-color: var(--accent); color: var(--accent); background: rgba(3, 218, 198, 0.1); }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(4px); z-index: 1000; align-items: center; justify-content: center; padding: 1rem; }
        .modal.active { display: flex; animation: fadeIn 0.3s ease; }
        .modal-content { background: var(--card-bg); width: 100%; max-width: 500px; border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); display: flex; flex-direction: column; overflow: hidden; }
        .modal-header { padding: 1.5rem; border-bottom: 1px solid var(--border); position: relative; }
        .modal-header h2 { font-size: 1.25rem; margin-bottom: 1rem; }
        .progress-bar { width: 100%; height: 8px; background: var(--bg-color); border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem; }
        .progress { height: 100%; background: var(--accent); width: 0%; transition: width 0.3s ease; }
        .progress-text { font-size: 0.85rem; color: var(--text-muted); }
        .close-btn { position: absolute; top: 1.5rem; right: 1.5rem; background: transparent; border: none; color: var(--text-muted); font-size: 1.25rem; cursor: pointer; transition: color 0.2s; }
        .close-btn:hover { color: var(--danger); }
        .modal-body { padding: 2rem 1.5rem; }
        .question-card { text-align: center; padding: 2rem; background: var(--bg-color); border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1.5rem; }
        .question-label { display: block; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px; }
        #question-word { font-size: 2.5rem; color: var(--primary); word-break: break-word; }
        #question-word.question-definition { font-size: 1.1rem !important; color: var(--text-main); line-height: 1.8; text-align: left; padding: 1.5rem; background: rgba(0, 0, 0, 0.2); border-radius: 8px; border-left: 4px solid var(--accent); margin-top: 1rem; font-weight: 400; }
        .answer-section { display: flex; flex-direction: column; gap: 1rem; }
        .answer-section input { text-align: center; font-size: 1.25rem; padding: 1rem; }
        .feedback { text-align: center; font-weight: 600; min-height: 24px; font-size: 1.1rem; }
        .feedback.correct { color: var(--success); animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .feedback.wrong { color: var(--danger); animation: shake 0.5s; }
        .modal-footer { padding: 1.5rem; border-top: 1px solid var(--border); display: flex; justify-content: stretch; }
        .modal-footer button { flex: 1; }

        .result-card { text-align: center; margin-bottom: 2rem; }
        .result-icon { font-size: 4rem; color: #fbbf24; margin-bottom: 1rem; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .score-display { font-size: 2.5rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.5rem; }
        #score-message { color: var(--text-muted); font-size: 1.1rem; }
        .wrong-answers { list-style: none; max-height: 200px; overflow-y: auto; padding-right: 0.5rem; }
        .wrong-answers::-webkit-scrollbar { width: 6px; }
        .wrong-answers::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
        .wrong-item { background: var(--bg-color); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 0.5rem; }
        .wrong-q { font-weight: 700; color: var(--danger); margin-bottom: 0.25rem; }
        .wrong-correct { color: var(--success); font-size: 0.9rem; }
        .wrong-user { color: var(--text-muted); font-size: 0.9rem; text-decoration: line-through; margin-left: 0.5rem; }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes popIn { 0% { opacity: 0; transform: scale(0.8); } 50% { transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); } 20%, 40%, 60%, 80% { transform: translateX(5px); } }
        </style>
    </head>
    <body>
        <div class="app-container">
            <header>
                <h1>영단어 마스터</h1>
                <p>나만의 영단어장과 테스트</p>
            </header>

            <div class="card">
                <h2>단어 추가</h2>
                <div class="input-group">
                    <div class="input-wrapper">
                        <label>영어 단어</label>
                        <input type="text" id="input-en" placeholder="Apple" autocomplete="off">
                    </div>
                    <div class="input-wrapper">
                        <label>뜻</label>
                        <input type="text" id="input-ko" placeholder="사과" autocomplete="off">
                    </div>
                    <button class="btn primary-btn" id="add-btn">추가</button>
                </div>
            </div>

            <div class="card">
                <div class="section-header">
                    <h2>나의 단어장</h2>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <span class="word-count" id="word-count">총 0개</span>
                        <button id="delete-all-btn" style="background: transparent; border: 1px solid var(--danger); color: var(--danger); padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(207, 102, 121, 0.1)'" onmouseout="this.style.background='transparent'">전체 삭제</button>
                    </div>
                </div>
                <div class="word-list-container">
                    <ul id="word-list">
                        <li class="empty-state">단어를 추가해주세요.</li>
                    </ul>
                </div>
            </div>

            <div class="card">
                <h2>테스트 시작</h2>
                <div class="test-options">
                    <div class="radio-group">
                        <input type="radio" id="mode-en-ko" name="test-mode" value="en-ko" checked>
                        <label for="mode-en-ko">영어 ➜ 한글</label>
                    </div>
                    <div class="radio-group">
                        <input type="radio" id="mode-ko-en" name="test-mode" value="ko-en">
                        <label for="mode-ko-en">한글 ➜ 영어</label>
                    </div>
                </div>
                <button class="btn accent-btn" id="start-test-btn" disabled>단어 1개 이상 필요</button>
            </div>
        </div>

        <!-- 퀴즈 모달 -->
        <div class="modal" id="quiz-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>테스트 진행 중</h2>
                    <button class="close-btn" id="close-modal">✖</button>
                    <div class="progress-bar"><div class="progress" id="progress-bar"></div></div>
                    <div class="progress-text" id="progress-text">1 / 5</div>
                </div>
                <div class="modal-body" id="modal-test-area">
                    <div class="question-card">
                        <span class="question-label" id="question-label">다음 단어의 뜻은?</span>
                        <div id="question-word">Apple</div>
                    </div>
                    <div class="answer-section">
                        <input type="text" id="answer-input" placeholder="정답 입력 후 엔터" autocomplete="off">
                        <div class="feedback" id="feedback-msg"></div>
                    </div>
                </div>
                <!-- 결과 영역 -->
                <div class="modal-body hidden" id="modal-result-area" style="display:none;">
                    <div class="result-card">
                        <div class="result-icon">🏆</div>
                        <div class="score-display" id="score-display">100점</div>
                        <div id="score-message">수고하셨습니다!</div>
                    </div>
                    <ul class="wrong-answers" id="wrong-answers"></ul>
                </div>
                <div class="modal-footer" id="modal-footer-test">
                    <button class="btn primary-btn" id="submit-answer-btn">제출 (Enter)</button>
                </div>
                <div class="modal-footer hidden" id="modal-footer-result" style="display:none;">
                    <button class="btn primary-btn" id="restart-btn">다시 하기</button>
                </div>
            </div>
        </div>

        <script>
            let words = [];
            let testWords = [];
            let currentQuestionIndex = 0;
            let correctCount = 0;
            let currentMode = "en-ko";
            let wrongAnswersArray = [];

            // DOM Elements
            const inputEn = document.getElementById('input-en');
            const inputKo = document.getElementById('input-ko');
            const addBtn = document.getElementById('add-btn');
            const wordList = document.getElementById('word-list');
            const wordCount = document.getElementById('word-count');
            const startTestBtn = document.getElementById('start-test-btn');
            
            // Modal Elements
            const quizModal = document.getElementById('quiz-modal');
            const closeModal = document.getElementById('close-modal');
            const modalTestArea = document.getElementById('modal-test-area');
            const modalResultArea = document.getElementById('modal-result-area');
            const modalFooterTest = document.getElementById('modal-footer-test');
            const modalFooterResult = document.getElementById('modal-footer-result');
            
            const questionLabel = document.getElementById('question-label');
            const questionWord = document.getElementById('question-word');
            const answerInput = document.getElementById('answer-input');
            const submitAnswerBtn = document.getElementById('submit-answer-btn');
            const feedbackMsg = document.getElementById('feedback-msg');
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const scoreDisplay = document.getElementById('score-display');
            const wrongAnswersList = document.getElementById('wrong-answers');
            const restartBtn = document.getElementById('restart-btn');

            function renderWords() {
                wordList.innerHTML = '';
                if(words.length === 0) {
                    wordList.innerHTML = '<li class="empty-state">단어를 추가해주세요.</li>';
                    startTestBtn.disabled = true;
                    startTestBtn.innerText = "단어 1개 이상 필요";
                } else {
                    words.forEach((w, idx) => {
                        const li = document.createElement('li');
                        li.className = 'word-item';
                        li.innerHTML = `
                            <div class="word-pair">
                                <span class="word-en">${w.en}</span>
                                <span class="word-ko">${w.ko}</span>
                            </div>
                            <button class="delete-btn" onclick="deleteWord(${idx})">✖</button>
                        `;
                        wordList.appendChild(li);
                    });
                    startTestBtn.disabled = false;
                    startTestBtn.innerText = "테스트 시작";
                }
                wordCount.innerText = `총 ${words.length}개`;
            }

            window.deleteWord = function(index) {
                words.splice(index, 1);
                renderWords();
            };

            const deleteAllBtn = document.getElementById('delete-all-btn');
            if (deleteAllBtn) {
                deleteAllBtn.addEventListener('click', () => {
                    if (words.length > 0 && confirm('단어장의 모든 단어를 정말 삭제하시겠습니까?')) {
                        words = [];
                        renderWords();
                    }
                });
            }

            addBtn.addEventListener('click', () => {
                const en = inputEn.value.trim();
                const ko = inputKo.value.trim();
                if(en && ko) {
                    words.push({en, ko});
                    inputEn.value = '';
                    inputKo.value = '';
                    inputEn.focus();
                    renderWords();
                }
            });

            inputKo.addEventListener('keypress', (e) => {
                if(e.key === 'Enter') addBtn.click();
            });

            startTestBtn.addEventListener('click', () => {
                currentMode = document.querySelector('input[name="test-mode"]:checked').value;
                testWords = [...words].sort(() => Math.random() - 0.5);
                currentQuestionIndex = 0;
                correctCount = 0;
                wrongAnswersArray = [];
                
                modalTestArea.style.display = "block";
                modalFooterTest.style.display = "flex";
                modalResultArea.style.display = "none";
                modalFooterResult.style.display = "none";
                
                quizModal.classList.add('active');
                loadQuestion();
            });

            closeModal.addEventListener('click', () => {
                quizModal.classList.remove('active');
            });

            function loadQuestion() {
                const word = testWords[currentQuestionIndex];
                if(currentMode === 'en-ko') {
                    questionLabel.innerText = "다음 단어의 뜻은?";
                    questionWord.innerText = word.en;
                    questionWord.className = "";
                } else {
                    questionLabel.innerText = "다음 뜻을 가진 영어 단어는?";
                    questionWord.innerText = word.ko;
                    questionWord.className = "question-definition";
                }
                
                answerInput.value = '';
                feedbackMsg.innerText = '';
                feedbackMsg.className = 'feedback';
                answerInput.disabled = false;
                submitAnswerBtn.disabled = false;
                
                const percent = (currentQuestionIndex / testWords.length) * 100;
                progressBar.style.width = percent + "%";
                progressText.innerText = `${currentQuestionIndex + 1} / ${testWords.length}`;
                
                setTimeout(() => answerInput.focus(), 100);
            }

            submitAnswerBtn.addEventListener('click', checkAnswer);
            answerInput.addEventListener('keypress', (e) => {
                if(e.key === 'Enter' && !answerInput.disabled) checkAnswer();
            });

            function checkAnswer() {
                const userAnswer = answerInput.value.trim().toLowerCase();
                if(!userAnswer) return;
                
                const word = testWords[currentQuestionIndex];
                let isCorrect = false;
                let correctAnswerStr = "";

                if(currentMode === 'en-ko') {
                    if(userAnswer.includes(word.ko) || word.ko.includes(userAnswer)) isCorrect = true;
                    correctAnswerStr = word.ko;
                } else {
                    if(userAnswer === word.en.toLowerCase()) isCorrect = true;
                    correctAnswerStr = word.en;
                }

                answerInput.disabled = true;
                submitAnswerBtn.disabled = true;

                if(isCorrect) {
                    feedbackMsg.innerText = "정답입니다! 🎉";
                    feedbackMsg.className = "feedback correct";
                    correctCount++;
                } else {
                    feedbackMsg.innerText = `틀렸습니다! 정답: ${correctAnswerStr}`;
                    feedbackMsg.className = "feedback wrong";
                    wrongAnswersArray.push({
                        q: currentMode === 'en-ko' ? word.en : word.ko,
                        user: userAnswer,
                        correct: correctAnswerStr
                    });
                }

                setTimeout(() => {
                    currentQuestionIndex++;
                    if(currentQuestionIndex < testWords.length) {
                        loadQuestion();
                    } else {
                        showResult();
                    }
                }, 1500);
            }

            function showResult() {
                progressBar.style.width = "100%";
                modalTestArea.style.display = "none";
                modalFooterTest.style.display = "none";
                modalResultArea.style.display = "block";
                modalFooterResult.style.display = "flex";

                const score = Math.round((correctCount / testWords.length) * 100);
                scoreDisplay.innerText = `${score}점`;

                wrongAnswersList.innerHTML = '';
                if(wrongAnswersArray.length === 0) {
                    const li = document.createElement('li');
                    li.className = 'empty-state';
                    li.innerHTML = '<div style="font-size:2rem;margin-bottom:0.5rem;">🎉</div>모두 맞췄습니다!';
                    wrongAnswersList.appendChild(li);
                } else {
                    wrongAnswersArray.forEach(w => {
                        const li = document.createElement('li');
                        li.className = 'wrong-item';
                        li.innerHTML = `
                            <div class="wrong-q">${w.q}</div>
                            <div>
                                <span class="wrong-correct">✔ ${w.correct}</span>
                                <span class="wrong-user">❌ ${w.user}</span>
                            </div>
                        `;
                        wrongAnswersList.appendChild(li);
                    });
                }
            }

            restartBtn.addEventListener('click', () => {
                quizModal.classList.remove('active');
            });
            
            // 초기 단어 설정용 코드 (옵션)
            words.push({en: "Extraterrestrial", ko: "외계의, 지구 밖의"});
            words.push({en: "Resilience", ko: "회복력, 탄성"});
            renderWords();
        </script>
    </body>
    </html>
    """
    
    # HTML을 Streamlit 상에 렌더링
    components.html(vocab_html, height=1000, scrolling=True)
    
    st.stop() # 메인 화면(학습 보조)을 숨기기 위해 앱 실행 중단


if api_key:
    client = OpenAI(api_key=api_key)

    @st.cache_data
    def extract_text_from_pdf(file_bytes):
        reader = PyPDF2.PdfReader(file_bytes)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    # Do not cache audio extraction because the temp file might be different internally, 
    # but more importantly Streamlit cache has file hashing bugs sometimes.
    def extract_text_from_audio(audio_file):
        # Whisper needs a file path or file-like object with a name
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
            tmp_file.write(audio_file.getvalue())
            tmp_file_path = tmp_file.name

        with open(tmp_file_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        os.remove(tmp_file_path)
        return transcript.text

    def generate_summary(text):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant. Summarize the following text into 5-10 key bullet points."},
                {"role": "user", "content": text}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content

    def generate_quiz(summary, quiz_type):
        prompt = f"Based on the following summary, generate exactly 5 quiz questions of type: {quiz_type}.\n\nSummary:\n{summary}\n\nQuestions should be helpful for a student studying this material. Provide the answers at the end."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant that generates quizzes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

    st.header("1. Upload Material")
    uploaded_file = st.file_uploader("Upload a PDF or Audio file (mp3, wav)", type=["pdf", "mp3", "wav"])

    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        st.write("Extracting text...")
        with st.spinner("Processing file..."):
            extracted_text = ""
            if file_extension == ".pdf":
                extracted_text = extract_text_from_pdf(uploaded_file)
            elif file_extension in [".mp3", ".wav"]:
                extracted_text = extract_text_from_audio(uploaded_file)

        if extracted_text:
            st.success("Text extracted successfully!")
            with st.expander("View Extracted Text", expanded=False):
                st.text_area("Extracted Text", extracted_text, height=200)

            # Store extracted text in session state
            st.session_state['extracted_text'] = extracted_text
            
            st.header("2. AI Summarization")
            if st.button("Summarize"):
                with st.spinner("Generating summary..."):
                    summary = generate_summary(st.session_state['extracted_text'])
                    st.session_state['summary'] = summary
            
            if 'summary' in st.session_state:
                st.subheader("Summary")
                st.markdown(st.session_state['summary'])

                st.header("3. Quiz Generator")
                quiz_type = st.radio(
                    "Choose a quiz type:",
                    ["Multiple Choice", "Short Answer", "True / False (O/X)"]
                )

                if st.button("Generate Quiz"):
                    with st.spinner(f"Generating {quiz_type} quiz..."):
                        quiz_content = generate_quiz(st.session_state['summary'], quiz_type)
                        st.subheader("Quiz")
                        st.markdown(quiz_content)
else:
    st.info("Waiting for API key.")
