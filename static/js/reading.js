// Interactive Reading JavaScript
class InteractiveReader {
    constructor() {
        this.currentSession = null;
        this.selectedMaterial = null;
        this.readingStartTime = null;
        this.currentWPM = 0;
        this.vocabularyClicks = 0;
        this.wordsRead = 0;
        this.totalWords = 0;
        this.chatbot = null;
        this.readingMode = null; // 'lock' or 'ai'
        this.comprehensionQuestions = [];
        this.currentQuestionIndex = 0;
        this.userAnswers = {};
        
        this.init();
    }
    
    init() {
        // Check authentication first
        if (!this.checkAuthentication()) {
            return; // Will redirect to login
        }

        // Only load materials and other authenticated content if we have a valid token
        this.loadMaterials();
        this.loadVocabularyStats();
        this.bindEvents();
        this.startProgressTracking();
        this.initializeChatbot();
        this.displayUserInfo();
    }
    
    checkAuthentication() {
        const token = this.getToken();
        if (!token) {
            // Redirect to login with current page as redirect target
            const currentUrl = encodeURIComponent(window.location.pathname);
            window.location.href = `/login?redirect=${currentUrl}`;
            return false;
        }
        return true;
    }
    
    bindEvents() {
        // Material selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.material-item')) {
                this.selectMaterial(e.target.closest('.material-item'));
            }
        });
        
        // Start reading
        document.getElementById('startReadingBtn').addEventListener('click', () => {
            this.showModeSelection();
        });
        
        // Reading mode selection
        document.getElementById('lockModeBtn').addEventListener('click', () => {
            this.selectReadingMode('lock');
        });
        
        document.getElementById('aiModeBtn').addEventListener('click', () => {
            this.selectReadingMode('ai');
        });
        
        // Complete reading
        document.getElementById('completeReadingBtn').addEventListener('click', () => {
            this.completeReading();
        });
        
        // Filter changes
        document.getElementById('categoryFilter').addEventListener('change', () => {
            this.loadMaterials();
        });
        
        document.getElementById('difficultyFilter').addEventListener('change', () => {
            this.loadMaterials();
        });
        
        // Word modal events
        document.getElementById('toggleChineseBtn').addEventListener('click', () => {
            this.toggleChineseTranslation();
        });
        
        document.getElementById('markMasteredBtn').addEventListener('click', () => {
            this.markWordAsMastered();
        });
        
        // Prevent text selection on double-click for Chinese translation
        document.addEventListener('dblclick', (e) => {
            if (e.target.classList.contains('interactive-word')) {
                e.preventDefault();
                // Check if we're in lock mode - if so, don't allow double-click translation
                if (this.readingMode === 'lock') {
                    return; // Block Chinese translation in lock mode
                }
                this.handleWordDoubleClick(e.target);
            }
        });
        
        // Question modal events
        document.getElementById('prevQuestionBtn').addEventListener('click', () => {
            this.showPreviousQuestion();
        });
        
        document.getElementById('nextQuestionBtn').addEventListener('click', () => {
            this.showNextQuestion();
        });
        
        document.getElementById('submitQuestionsBtn').addEventListener('click', () => {
            this.submitAnswers();
        });
        
        document.getElementById('selectNewArticleBtn').addEventListener('click', () => {
            this.selectNewArticle();
        });
        
        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });
    }
    
    async loadMaterials() {
        const category = document.getElementById('categoryFilter').value;
        const difficulty = document.getElementById('difficultyFilter').value;
        
        try {
            const params = new URLSearchParams();
            if (category) params.append('category', category);
            if (difficulty) params.append('difficulty', difficulty);
            
            const response = await fetch(`/api/reading/materials?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.status === 401) {
                // Token is invalid or expired, redirect to login
                const currentUrl = encodeURIComponent(window.location.pathname);
                window.location.href = `/login?redirect=${currentUrl}`;
                return;
            }

            const data = await response.json();

            if (data.success) {
                this.renderMaterials(data.materials);
            } else {
                console.error('Failed to load materials:', data.error);
                this.showError('Failed to load reading materials');
            }
        } catch (error) {
            console.error('Error loading materials:', error);
            this.showError('Network error loading materials');
        }
    }
    
    renderMaterials(materials) {
        const container = document.getElementById('materialsList');
        
        if (materials.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-3">
                    <i class="bi bi-search"></i>
                    <p class="mt-2">No materials found with current filters</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = materials.map(material => `
            <div class="material-item difficulty-${material.difficulty_level}" data-material-id="${material.id}">
                <div class="material-title">${material.title}</div>
                <div class="material-meta">
                    <i class="bi bi-clock"></i> ${material.estimated_reading_time} min | 
                    <i class="bi bi-file-text"></i> ${material.word_count} words
                </div>
                <div class="material-tags">
                    <span class="badge bg-primary">${material.difficulty_level}</span>
                    <span class="badge bg-secondary">${material.category}</span>
                    ${(material.target_exams || []).map(exam => 
                        `<span class="badge bg-success">${exam}</span>`
                    ).join('')}
                </div>
            </div>
        `).join('');
    }
    
    async selectMaterial(element) {
        // Remove previous selection
        document.querySelectorAll('.material-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selection to clicked item
        element.classList.add('selected');
        
        const materialId = parseInt(element.dataset.materialId);
        
        try {
            // Fetch full material data including content
            const response = await fetch(`/api/reading/materials/${materialId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.selectedMaterial = data.material;
                
                // Show reading header
                document.getElementById('readingHeader').style.display = 'block';
                document.getElementById('instructions').style.display = 'block';
                
                // Update header with material info
                document.getElementById('textTitle').textContent = this.selectedMaterial.title;
                document.getElementById('textDifficulty').textContent = this.selectedMaterial.difficulty_level.charAt(0).toUpperCase() + this.selectedMaterial.difficulty_level.slice(1);
                document.getElementById('textCategory').textContent = this.selectedMaterial.category.charAt(0).toUpperCase() + this.selectedMaterial.category.slice(1);
                document.getElementById('textWordCount').textContent = `${this.selectedMaterial.word_count} words`;
                document.getElementById('estimatedTime').textContent = `~${this.selectedMaterial.estimated_reading_time} min read`;
                
            } else {
                console.error('Failed to load material:', data.error);
                alert('Failed to load reading material. Please try again.');
            }
            
        } catch (error) {
            console.error('Error loading material:', error);
            alert('Network error loading material. Please check your connection.');
        }
    }
    
    async startReading() {
        if (!this.selectedMaterial) {
            this.showError('Please select a reading material first');
            return;
        }
        
        try {
            const response = await fetch('/api/reading/session/start', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    material_id: this.selectedMaterial
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.readingStartTime = Date.now();
                this.totalWords = data.interactive_text.total_words;
                
                this.renderInteractiveText(data.interactive_text);
                this.showReadingProgress();
                
                // Show chatbot for reading assistance
                document.getElementById('readingChatbot').style.display = 'block';
                
                // Hide instructions and start button
                document.getElementById('instructions').style.display = 'none';
                document.getElementById('startReadingBtn').style.display = 'none';
                document.getElementById('completeReadingBtn').style.display = 'inline-block';
                
            } else {
                this.showError(data.error || 'Failed to start reading session');
            }
        } catch (error) {
            console.error('Error starting reading:', error);
            this.showError('Network error starting reading session');
        }
    }
    
    renderInteractiveText(interactiveText) {
        const container = document.getElementById('interactiveText');
        
        const html = interactiveText.sentences.map(sentence => {
            const wordsHtml = sentence.words.map(wordObj => {
                if (wordObj.clickable) {
                    return `<span class="interactive-word" data-word="${wordObj.text}">${wordObj.text}</span>`;
                } else {
                    return wordObj.text;
                }
            }).join('');
            
            return `<div class="interactive-sentence">${wordsHtml}</div>`;
        }).join('');
        
        container.innerHTML = html;
        
        // Bind word click events
        container.addEventListener('click', (e) => {
            if (e.target.classList.contains('interactive-word')) {
                // Check if we're in lock mode - if so, don't allow word clicks
                if (this.readingMode === 'lock') {
                    return; // Block word clicks in lock mode
                }
                this.handleWordClick(e.target);
            }
        });
        
        // Bind right-click for chatbot text explanation
        container.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            // Check if we're in lock mode - if so, don't allow text selection help
            if (this.readingMode === 'lock') {
                return; // Block text selection help in lock mode
            }
            this.handleTextSelection(e);
        });
        
        // Bind text selection for AI explanation
        container.addEventListener('mouseup', () => {
            // Check if we're in lock mode - if so, don't allow text selection help
            if (this.readingMode === 'lock') {
                return; // Block text selection help in lock mode
            }
            this.handleTextSelection();
        });
    }
    
    async handleWordClick(wordElement) {
        const word = wordElement.dataset.word;
        
        // Add animation
        wordElement.classList.add('animate-click');
        setTimeout(() => wordElement.classList.remove('animate-click'), 300);
        
        // Mark as clicked
        wordElement.classList.add('clicked');
        this.vocabularyClicks++;
        
        try {
            const response = await fetch(`/api/reading/session/${this.currentSession}/word-click`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word,
                    include_chinese: false
                })
            });
            
            // Check if response is ok first
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Always check if word_data exists first, regardless of success flag
            if (data.word_data && data.word_data.word) {
                this.showWordModal(data.word_data);
            } else if (data.success) {
                // If success is true but no word_data, something is wrong
                console.error('API returned success but no word data:', data);
                this.showError(`Sorry, couldn't retrieve information for "${word}". Please try again.`);
            } else {
                // Only show error if we have no word data at all
                console.error('Word API response error:', data);
                this.showError(data.error || `Sorry, couldn't find information for "${word}". Please try again.`);
            }
        } catch (error) {
            console.error('Error handling word click:', error);
            // Only show error for severe network issues, otherwise provide fallback
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                this.showError(`Network error - please check your internet connection.`);
            } else {
                // For all other errors, just provide fallback word data silently
                console.warn(`Providing fallback data for word "${word}" due to:`, error.message);
                this.showWordModal({
                    word: word,
                    definition: `A word meaning: ${word}`,
                    pronunciation: `/${word.toLowerCase()}/`,
                    examples: [`This is an example sentence using the word "${word}".`],
                    synonyms: ['related_word'],
                    difficulty_level: 'Medium',
                    looked_up_count: 1
                });
            }
        }
    }
    
    async handleWordDoubleClick(wordElement) {
        const word = wordElement.dataset.word;
        
        try {
            const response = await fetch(`/api/reading/session/${this.currentSession}/word-click`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word,
                    include_chinese: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.word_data) {
                this.showWordModal(data.word_data, true);
            } else {
                console.error('Chinese translation API error:', data);
                // For double-click, just show the regular modal without Chinese translation
                this.showWordModal({
                    word: word,
                    definition: 'Definition not available',
                    chinese_translation: 'Translation not available'
                }, true);
            }
        } catch (error) {
            console.error('Error getting Chinese translation:', error);
            // Still show modal with basic info
            this.showWordModal({
                word: word,
                definition: 'Definition not available',
                chinese_translation: 'Translation not available'
            }, true);
        }
    }
    
    showWordModal(wordData, showChinese = false) {
        if (!wordData || !wordData.word) {
            console.error('Invalid word data:', wordData);
            this.showError('Invalid word data received');
            return;
        }
        
        this.currentWordData = wordData;
        
        // Update modal content with safe fallbacks
        document.getElementById('modalWord').textContent = wordData.word || 'Unknown word';
        document.getElementById('definitionText').textContent = wordData.definition || 'Definition not available';
        document.getElementById('pronunciationText').textContent = wordData.pronunciation || 'Pronunciation not available';
        document.getElementById('wordDifficulty').textContent = wordData.difficulty_level || 'N/A';
        document.getElementById('lookupCount').textContent = wordData.looked_up_count || 1;
        
        // Examples
        const examplesList = document.getElementById('examplesList');
        if (wordData.examples && Array.isArray(wordData.examples) && wordData.examples.length > 0) {
            examplesList.innerHTML = wordData.examples.map(example => 
                `<li>${example}</li>`
            ).join('');
        } else {
            examplesList.innerHTML = '<li class="text-muted">No examples available</li>';
        }
        
        // Synonyms
        const synonymsList = document.getElementById('synonymsList');
        if (wordData.synonyms && Array.isArray(wordData.synonyms) && wordData.synonyms.length > 0) {
            synonymsList.innerHTML = wordData.synonyms.map(synonym => 
                `<span class="badge bg-light text-dark">${synonym}</span>`
            ).join('');
        } else {
            synonymsList.innerHTML = '<span class="text-muted">No related words available</span>';
        }
        
        // Chinese translation
        const chineseDiv = document.getElementById('chineseTranslation');
        if (showChinese && wordData.chinese_translation) {
            document.getElementById('chineseText').textContent = wordData.chinese_translation;
            chineseDiv.style.display = 'block';
        } else {
            chineseDiv.style.display = 'none';
        }
        
        // Show modal
        try {
            const modal = new bootstrap.Modal(document.getElementById('wordModal'));
            modal.show();
        } catch (error) {
            console.error('Error showing word modal:', error);
            this.showError('Error displaying word information');
        }
    }
    
    async toggleChineseTranslation() {
        if (!this.currentWordData) return;
        
        const chineseDiv = document.getElementById('chineseTranslation');
        if (chineseDiv.style.display === 'none') {
            // Get Chinese translation
            try {
                const response = await fetch(`/api/reading/session/${this.currentSession}/word-click`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        word: this.currentWordData.word,
                        include_chinese: true
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.word_data.chinese_translation) {
                    document.getElementById('chineseText').textContent = data.word_data.chinese_translation;
                    chineseDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error getting Chinese translation:', error);
            }
        } else {
            chineseDiv.style.display = 'none';
        }
    }
    
    async markWordAsMastered() {
        if (!this.currentWordData) return;
        
        try {
            const response = await fetch('/api/reading/vocabulary/master', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: this.currentWordData.word
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update UI to show word as mastered
                const wordElements = document.querySelectorAll(`[data-word="${this.currentWordData.word}"]`);
                wordElements.forEach(el => el.classList.add('vocab-mastered'));
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('wordModal'));
                modal.hide();
                
                // Refresh vocabulary stats
                this.loadVocabularyStats();
                
                this.showSuccess(`Word "${this.currentWordData.word}" marked as mastered!`);
            }
        } catch (error) {
            console.error('Error marking word as mastered:', error);
        }
    }
    
    showReadingProgress() {
        document.getElementById('progressContainer').style.display = 'block';
    }
    
    updateProgress() {
        if (!this.currentSession || !this.readingStartTime) return;
        
        const timeElapsed = (Date.now() - this.readingStartTime) / 1000; // seconds
        const minutes = Math.floor(timeElapsed / 60);
        const seconds = Math.floor(timeElapsed % 60);
        
        document.getElementById('readingTime').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // Calculate WPM (rough estimate based on scroll position)
        const scrollPercent = this.calculateScrollProgress();
        const wordsRead = Math.floor(this.totalWords * scrollPercent / 100);
        
        if (timeElapsed > 0) {
            this.currentWPM = Math.floor((wordsRead * 60) / timeElapsed);
            document.getElementById('currentWPM').textContent = this.currentWPM;
        }
        
        // Update progress bar
        const progressBar = document.getElementById('readingProgress');
        progressBar.style.width = `${scrollPercent}%`;
        progressBar.setAttribute('aria-valuenow', scrollPercent);
        progressBar.textContent = `${Math.floor(scrollPercent)}% Complete`;
        
        // Send progress update to server
        this.updateServerProgress({
            words_read: wordsRead,
            time_spent: timeElapsed,
            completion_percentage: scrollPercent,
            vocabulary_clicks: this.vocabularyClicks
        });
    }
    
    calculateScrollProgress() {
        const container = document.getElementById('interactiveText');
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        
        if (scrollHeight <= 0) return 0;
        
        return Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100));
    }
    
    async updateServerProgress(progressData) {
        try {
            await fetch(`/api/reading/session/${this.currentSession}/progress`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(progressData)
            });
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }
    
    async completeReading() {
        if (!this.currentSession) return;
        
        const timeElapsed = (Date.now() - this.readingStartTime) / 1000;
        const scrollPercent = this.calculateScrollProgress();
        const wordsRead = Math.floor(this.totalWords * scrollPercent / 100);
        
        try {
            const response = await fetch(`/api/reading/session/${this.currentSession}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    total_time: timeElapsed,
                    completion_percentage: scrollPercent,
                    vocabulary_clicks: this.vocabularyClicks,
                    new_words_learned: document.querySelectorAll('.interactive-word.clicked').length
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showCompletionSummary(data);
            } else {
                this.showError(data.error || 'Failed to complete reading session');
            }
        } catch (error) {
            console.error('Error completing reading:', error);
            this.showError('Network error completing reading session');
        }
    }
    
    showCompletionSummary(data) {
        const summary = data.session_summary;
        const recommendations = data.recommendations || [];
        
        let summaryHtml = `
            <div class="alert alert-success">
                <h5><i class="bi bi-check-circle"></i> Reading Session Complete!</h5>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6>Your Performance</h6>
                        <ul class="list-unstyled">
                            <li><strong>Reading Time:</strong> ${summary.reading_time_minutes} minutes</li>
                            <li><strong>Reading Speed:</strong> ${summary.words_per_minute} WPM</li>
                            <li><strong>Completion:</strong> ${summary.completion_percentage}%</li>
                            <li><strong>Vocabulary Interactions:</strong> ${summary.vocabulary_interactions}</li>
                            <li><strong>New Words Learned:</strong> ${summary.new_words_learned}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Recommendations</h6>
                        <ul>
                            ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
        
        // Show comprehension questions if available
        if (data.comprehension_questions && data.comprehension_questions.length > 0) {
            summaryHtml += `
                <div class="alert alert-info">
                    <h6>Comprehension Questions</h6>
                    <p>Answer these questions to test your understanding:</p>
                    <!-- Questions would be rendered here -->
                </div>
            `;
        }
        
        document.getElementById('interactiveText').innerHTML = summaryHtml;
        
        // Reset session
        this.currentSession = null;
        this.readingStartTime = null;
        document.getElementById('progressContainer').style.display = 'none';
        document.getElementById('completeReadingBtn').style.display = 'none';
        document.getElementById('startReadingBtn').style.display = 'inline-block';
        
        // Hide chatbot when session ends
        document.getElementById('readingChatbot').style.display = 'none';
        
        // Refresh stats
        this.loadVocabularyStats();
    }
    
    async loadVocabularyStats() {
        try {
            const response = await fetch('/api/reading/vocabulary/stats', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
                // Token is invalid or expired, redirect to login
                const currentUrl = encodeURIComponent(window.location.pathname);
                window.location.href = `/login?redirect=${currentUrl}`;
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                document.getElementById('wordsLookedUp').textContent = data.stats.words_looked_up || 0;
                document.getElementById('wordsMastered').textContent = data.stats.words_mastered || 0;
                document.getElementById('vocabularySize').textContent = data.stats.vocabulary_size || 0;
            }
        } catch (error) {
            console.error('Error loading vocabulary stats:', error);
        }
    }
    
    startProgressTracking() {
        // Update progress every 2 seconds during reading
        setInterval(() => {
            if (this.currentSession && this.readingStartTime) {
                this.updateProgress();
            }
        }, 2000);
    }
    
    getToken() {
        return localStorage.getItem('auth_token') || null;
    }
    
    showError(message) {
        // Better error display using toast notification
        this.showToast(message, 'error');
    }
    
    showSuccess(message) {
        // Better success display using toast notification
        this.showToast(message, 'success');
    }
    
    showToast(message, type = 'info') {
        // Create toast notification instead of alert
        const toastId = 'toast-' + Date.now();
        const toastClass = type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-info';
        const iconClass = type === 'error' ? 'bi-exclamation-triangle-fill' : type === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill';
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${toastClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${iconClass} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Add toast to container
        toastContainer.insertAdjacentHTML('afterbegin', toastHtml);
        
        // Show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: type === 'error' ? 5000 : 3000 // Error messages stay longer
        });
        
        toast.show();
        
        // Remove element after toast is hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    // Chatbot functionality
    initializeChatbot() {
        this.chatbot = new ReadingChatbot(this);
    }
    
    displayUserInfo() {
        const username = localStorage.getItem('username') || 'Student';
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement) {
            userInfoElement.textContent = username;
        }
    }
    
    logout() {
        // Clear stored authentication data
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('username');
        localStorage.removeItem('user_type');
        
        // Redirect to home page
        window.location.href = '/';
    }
    
    handleTextSelection(e = null) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        if (selectedText.length > 0 && selectedText.length <= 500) {
            // Show floating tooltip for selected text
            this.showSelectionTooltip(selectedText, e);
        } else {
            // Hide tooltip if no selection
            this.hideSelectionTooltip();
        }
    }
    
    showSelectionTooltip(text, event) {
        // Remove existing tooltip
        this.hideSelectionTooltip();
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.id = 'textSelectionTooltip';
        tooltip.className = 'position-fixed bg-primary text-white p-2 rounded shadow';
        tooltip.style.zIndex = '9999';
        tooltip.style.fontSize = '12px';
        tooltip.style.cursor = 'pointer';
        tooltip.innerHTML = `
            <i class="bi bi-robot"></i> Ask AI about this text
        `;
        
        // Position tooltip
        if (event) {
            tooltip.style.left = event.pageX + 'px';
            tooltip.style.top = (event.pageY - 40) + 'px';
        } else {
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const rect = range.getBoundingClientRect();
                tooltip.style.left = (rect.left + rect.width / 2) + 'px';
                tooltip.style.top = (rect.top - 40) + 'px';
            }
        }
        
        // Add click handler
        tooltip.addEventListener('click', () => {
            this.explainSelectedText(text);
            this.hideSelectionTooltip();
        });
        
        document.body.appendChild(tooltip);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideSelectionTooltip();
        }, 5000);
    }
    
    hideSelectionTooltip() {
        const existing = document.getElementById('textSelectionTooltip');
        if (existing) {
            existing.remove();
        }
    }
    
    explainSelectedText(text) {
        // Open chatbot if not visible
        if (this.chatbot && !this.chatbot.isVisible) {
            this.chatbot.toggleChatbot();
        }
        
        // Send explanation request
        if (this.chatbot) {
            const message = `Can you explain this text: "${text}"`;
            this.chatbot.addMessage(message, 'user');
            this.chatbot.sendMessageToAPI(message);
        }
    }
}

// Reading Chatbot Class
class ReadingChatbot {
    constructor(reader) {
        this.reader = reader;
        this.isVisible = false;
        this.messageCount = 0;
        
        this.bindChatbotEvents();
    }
    
    bindChatbotEvents() {
        // Toggle chatbot
        document.getElementById('chatbotToggle').addEventListener('click', () => {
            this.toggleChatbot();
        });
        
        // Minimize chatbot
        document.getElementById('minimizeChatBtn').addEventListener('click', () => {
            this.toggleChatbot();
        });
        
        // Clear chat
        document.getElementById('clearChatBtn').addEventListener('click', () => {
            this.clearChat();
        });
        
        // Send message
        document.getElementById('sendChatBtn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key to send
        document.getElementById('chatbotInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.closest('.quick-action-btn').dataset.action;
                this.handleQuickAction(action);
            });
        });
    }
    
    showChatbot() {
        if (!this.reader.currentSession) {
            this.reader.showError('Please start a reading session first to use the AI assistant.');
            return;
        }
        
        document.getElementById('readingChatbot').style.display = 'block';
        this.toggleChatbot();
    }
    
    toggleChatbot() {
        const window = document.getElementById('chatbotWindow');
        this.isVisible = !this.isVisible;
        
        if (this.isVisible) {
            window.style.display = 'block';
            // Focus on input
            setTimeout(() => {
                document.getElementById('chatbotInput').focus();
            }, 300);
        } else {
            window.style.display = 'none';
        }
        
        // Reset badge count when opened
        if (this.isVisible) {
            this.messageCount = 0;
            this.updateBadge();
        }
    }
    
    updateBadge() {
        const badge = document.getElementById('chatbotBadge');
        badge.textContent = this.messageCount;
        badge.style.display = this.messageCount > 0 ? 'flex' : 'none';
    }
    
    async sendMessage() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        if (!this.reader.currentSession) {
            this.addMessage('Please start a reading session first so I can help you better!', 'assistant');
            return;
        }
        
        // Clear input and add user message
        input.value = '';
        this.addMessage(message, 'user');
        
        await this.sendMessageToAPI(message);
    }
    
    async sendMessageToAPI(message) {
        // Show typing indicator
        this.showTyping(true);
        
        try {
            const response = await fetch(`/api/reading/session/${this.reader.currentSession}/chatbot/ask`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.reader.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    type: 'general'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage(data.chatbot_response.response, 'assistant', data.chatbot_response.type);
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            }
        } catch (error) {
            console.error('Error sending message to chatbot:', error);
            this.addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'assistant');
        } finally {
            this.showTyping(false);
        }
    }
    
    async handleQuickAction(action) {
        if (!this.reader.currentSession) {
            this.addMessage('Please start a reading session first!', 'assistant');
            return;
        }
        
        // Use the regular message system instead of separate API calls
        let message = '';
        switch (action) {
            case 'tips':
                message = 'Can you give me some useful English learning tips?';
                break;
            case 'explain':
                message = 'I have a question about English. Can you help me?';
                break;
            case 'summarize':
                message = 'Can you summarize the main points of this text?';
                break;
        }
        
        if (message) {
            // Add user message and process through normal flow
            this.addMessage(message, 'user');
            await this.sendMessageToAPI(message);
        }
    }
    
    async explainWordInContext(word, sentenceContext = '') {
        if (!this.reader.currentSession) return;
        
        // Show the chatbot and add the word explanation request
        if (!this.isVisible) {
            this.toggleChatbot();
        }
        
        this.addMessage(`Explain the word "${word}"`, 'user');
        this.showTyping(true);
        
        try {
            const response = await fetch(`/api/reading/session/${this.reader.currentSession}/chatbot/explain-word`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.reader.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: word,
                    sentence_context: sentenceContext
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage(data.explanation.response, 'assistant', 'word-explanation');
            } else {
                this.addMessage(`I couldn't find detailed information about "${word}" right now.`, 'assistant');
            }
        } catch (error) {
            console.error('Error explaining word:', error);
            this.addMessage('Sorry, I had trouble explaining that word.', 'assistant');
        } finally {
            this.showTyping(false);
        }
    }
    
    addMessage(content, sender, type = '') {
        const messagesContainer = document.getElementById('chatbotMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = sender === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = `message-content ${type}`;
        
        // Convert simple markdown-like formatting
        const formattedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom smoothly
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
        
        // Update badge if chatbot is minimized and it's an assistant message
        if (!this.isVisible && sender === 'assistant') {
            this.messageCount++;
            this.updateBadge();
        }
    }
    
    showTyping(show) {
        const typingDiv = document.getElementById('chatbotTyping');
        typingDiv.style.display = show ? 'flex' : 'none';
    }
    
    clearChat() {
        const messagesContainer = document.getElementById('chatbotMessages');
        // Keep only the initial welcome message
        const welcomeMessage = messagesContainer.querySelector('.assistant-message');
        messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            messagesContainer.appendChild(welcomeMessage);
        }
    }
}

// Reading Mode and Comprehension Methods
InteractiveReader.prototype.showModeSelection = function() {
    if (!this.selectedMaterial) {
        alert('Please select a reading material first!');
        return;
    }
    
    // Show the mode selection section
    document.getElementById('readingModeSelection').style.display = 'block';
    
    // Scroll to mode selection
    document.getElementById('readingModeSelection').scrollIntoView({ 
        behavior: 'smooth',
        block: 'center'
    });
};

InteractiveReader.prototype.selectReadingMode = function(mode) {
    this.readingMode = mode;
    
    // Hide mode selection
    document.getElementById('readingModeSelection').style.display = 'none';
    
    // Start reading based on mode
    this.startReading();
};

InteractiveReader.prototype.startReading = async function() {
    if (!this.selectedMaterial || !this.readingMode) {
        return;
    }
    
    try {
        // Create reading session
        const response = await fetch('/api/reading/session/start', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                material_id: this.selectedMaterial.id,
                reading_mode: this.readingMode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.currentSession = data.session_id;
            
            // Configure based on reading mode
            if (this.readingMode === 'lock') {
                this.configureLockMode();
            } else {
                this.configureAIMode();
            }
            
            // Load the interactive text
            this.renderInteractiveText(data.interactive_text);
            
            // Continue with existing reading logic
            this.readingStartTime = Date.now();
            this.totalWords = this.selectedMaterial.word_count || 0;
            
            // Show reading interface elements
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('startReadingBtn').style.display = 'none';
            document.getElementById('completeReadingBtn').style.display = 'inline-block';
            
            // Start progress tracking
            this.startProgressTracking();
            
        } else {
            console.error('Failed to start reading session:', data.error);
            alert('Failed to start reading session. Please try again.');
        }
        
    } catch (error) {
        console.error('Error starting reading:', error);
        alert('Network error starting reading session. Please check your connection.');
    }
};

InteractiveReader.prototype.configureLockMode = function() {
    // Disable word clicking
    this.disableWordInteractions();
    
    // Hide chatbot
    document.getElementById('readingChatbot').style.display = 'none';
    
    // Update instructions
    const instructionsElement = document.getElementById('instructions');
    instructionsElement.innerHTML = `
        <h5><i class="bi bi-lock text-warning"></i> Lock Mode - Challenge Yourself!</h5>
        <div class="alert alert-warning">
            <strong>📚 Reading Challenge:</strong> You're in Lock Mode! No assistance available.
            <ul class="mb-0 mt-2">
                <li>❌ No word definitions or translations</li>
                <li>❌ No AI chatbot help</li>
                <li>✅ Focus on understanding through context</li>
                <li>✅ Complete 5 comprehension questions when finished</li>
            </ul>
        </div>
    `;
    instructionsElement.className = 'alert alert-warning';
};

InteractiveReader.prototype.configureAIMode = function() {
    // Enable all interactions (default behavior)
    this.enableWordInteractions();
    
    // Show chatbot
    document.getElementById('readingChatbot').style.display = 'block';
    
    // Keep original instructions
    const instructionsElement = document.getElementById('instructions');
    instructionsElement.innerHTML = `
        <h5><i class="bi bi-robot text-primary"></i> AI Assisted Mode</h5>
        <div class="alert alert-success">
            <strong>🤖 Full Assistance Available:</strong>
            <ul class="mb-0 mt-2">
                <li>✅ Click words for definitions and examples</li>
                <li>✅ Double-click for Chinese translations</li>
                <li>✅ Ask the AI chatbot any questions</li>
                <li>✅ Get help with vocabulary and comprehension</li>
            </ul>
        </div>
    `;
    instructionsElement.className = 'alert alert-success';
};

InteractiveReader.prototype.disableWordInteractions = function() {
    // Remove click events from words and make it clear they're not clickable
    const interactiveWords = document.querySelectorAll('.interactive-word');
    interactiveWords.forEach(word => {
        word.style.cursor = 'text';
        word.style.pointerEvents = 'none';
        word.style.color = 'inherit'; // Remove any special coloring
        word.style.textDecoration = 'none'; // Remove underlines
        word.removeAttribute('title');
        // Remove interactive styling
        word.classList.remove('interactive-word');
        word.classList.add('locked-word');
    });
};

InteractiveReader.prototype.enableWordInteractions = function() {
    // Enable click events for words (including previously locked ones)
    const allWords = document.querySelectorAll('.interactive-word, .locked-word');
    allWords.forEach(word => {
        word.style.cursor = 'pointer';
        word.style.pointerEvents = 'auto';
        word.setAttribute('title', 'Click for definition');
        // Restore interactive styling
        word.classList.remove('locked-word');
        word.classList.add('interactive-word');
    });
};

InteractiveReader.prototype.completeReading = function() {
    if (this.readingMode === 'lock') {
        // Show comprehension questions for lock mode
        this.showComprehensionQuestions();
    } else {
        // Show normal completion for AI mode
        this.showReadingComplete();
    }
};

InteractiveReader.prototype.showComprehensionQuestions = async function() {
    try {
        // Show loading in modal
        const modal = new bootstrap.Modal(document.getElementById('questionsModal'));
        modal.show();
        
        // Generate questions using AI
        const response = await fetch(`/api/reading/session/${this.currentSession}/questions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                material_id: this.selectedMaterial.id,
                text_content: this.selectedMaterial.content,
                num_questions: 5
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.comprehensionQuestions = data.questions;
            this.renderQuestions();
        } else {
            throw new Error(data.message || 'Failed to generate questions');
        }
        
    } catch (error) {
        console.error('Error loading questions:', error);
        document.getElementById('questionsContainer').innerHTML = `
            <div class="alert alert-danger">
                <h6>Error Loading Questions</h6>
                <p>Could not generate comprehension questions. Please try again.</p>
                <button class="btn btn-outline-danger" onclick="location.reload()">Refresh Page</button>
            </div>
        `;
    }
};

InteractiveReader.prototype.renderQuestions = function() {
    if (!this.comprehensionQuestions.length) return;
    
    this.currentQuestionIndex = 0;
    this.userAnswers = {};
    
    // Setup question numbers
    const questionNumbers = document.getElementById('questionNumbers');
    questionNumbers.innerHTML = '';
    
    for (let i = 0; i < this.comprehensionQuestions.length; i++) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-outline-secondary btn-sm';
        btn.textContent = i + 1;
        btn.onclick = () => this.showQuestion(i);
        questionNumbers.appendChild(btn);
    }
    
    // Show first question
    this.showQuestion(0);
    
    // Show navigation
    document.getElementById('questionNavigation').style.display = 'flex';
    
    // Update totals
    document.getElementById('totalQuestions').textContent = this.comprehensionQuestions.length;
    document.getElementById('totalQuestionsFooter').textContent = this.comprehensionQuestions.length;
};

InteractiveReader.prototype.showQuestion = function(index) {
    if (index < 0 || index >= this.comprehensionQuestions.length) return;
    
    this.currentQuestionIndex = index;
    const question = this.comprehensionQuestions[index];
    
    // Update question display
    document.getElementById('currentQuestionNum').textContent = index + 1;
    
    // Render question
    const container = document.getElementById('questionsContainer');
    container.innerHTML = `
        <div class="question-card">
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">Question ${index + 1}</h6>
                    <p class="question-text">${question.question}</p>
                    
                    <div class="options mt-3">
                        ${question.options.map((option, i) => `
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" 
                                       name="q${index}" value="${option}" id="q${index}_${i}"
                                       ${this.userAnswers[index] === option ? 'checked' : ''}>
                                <label class="form-check-label" for="q${index}_${i}">
                                    ${option}
                                </label>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners for this question
    const radioInputs = container.querySelectorAll(`input[name="q${index}"]`);
    radioInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            this.userAnswers[index] = e.target.value;
            this.updateAnswerProgress();
        });
    });
    
    // Update navigation buttons
    document.getElementById('prevQuestionBtn').disabled = index === 0;
    document.getElementById('nextQuestionBtn').disabled = index === this.comprehensionQuestions.length - 1;
    
    // Update question number buttons
    const numberButtons = document.getElementById('questionNumbers').children;
    Array.from(numberButtons).forEach((btn, i) => {
        btn.className = i === index ? 'btn btn-primary btn-sm' : 
                       this.userAnswers[i] !== undefined ? 'btn btn-success btn-sm' : 'btn btn-outline-secondary btn-sm';
    });
};

InteractiveReader.prototype.showPreviousQuestion = function() {
    if (this.currentQuestionIndex > 0) {
        this.showQuestion(this.currentQuestionIndex - 1);
    }
};

InteractiveReader.prototype.showNextQuestion = function() {
    if (this.currentQuestionIndex < this.comprehensionQuestions.length - 1) {
        this.showQuestion(this.currentQuestionIndex + 1);
    }
};

InteractiveReader.prototype.updateAnswerProgress = function() {
    const answeredCount = Object.keys(this.userAnswers).length;
    document.getElementById('answeredCount').textContent = answeredCount;
    
    // Enable submit button if all questions answered
    const submitBtn = document.getElementById('submitQuestionsBtn');
    submitBtn.disabled = answeredCount < this.comprehensionQuestions.length;
};

InteractiveReader.prototype.submitAnswers = async function() {
    try {
        const response = await fetch(`/api/reading/session/${this.currentSession}/submit-answers`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answers: this.userAnswers,
                questions: this.comprehensionQuestions
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.showResults(data.results);
        } else {
            throw new Error(data.message || 'Failed to submit answers');
        }
        
    } catch (error) {
        console.error('Error submitting answers:', error);
        alert('Error submitting answers. Please try again.');
    }
};

InteractiveReader.prototype.showResults = function(results) {
    // Hide questions modal
    bootstrap.Modal.getInstance(document.getElementById('questionsModal')).hide();
    
    // Show results modal
    const resultsModal = new bootstrap.Modal(document.getElementById('resultsModal'));
    
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="text-center mb-4">
            <div class="display-4 ${results.score >= 80 ? 'text-success' : results.score >= 60 ? 'text-warning' : 'text-danger'}">
                ${results.score}%
            </div>
            <h5>Your Comprehension Score</h5>
            <p class="text-muted">${results.correct_answers} out of ${results.total_questions} correct</p>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6><i class="bi bi-graph-up text-success"></i> Reading Performance</h6>
                        <ul class="list-unstyled">
                            <li>📖 Reading Time: ${Math.round((Date.now() - this.readingStartTime) / 60000)} minutes</li>
                            <li>⚡ Average WPM: ${this.currentWPM}</li>
                            <li>🎯 Comprehension: ${results.score}%</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6><i class="bi bi-lightbulb text-primary"></i> Feedback</h6>
                        <p class="small">${results.feedback || this.getScoreFeedback(results.score)}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <h6>Question Review</h6>
            ${this.renderQuestionReview(results)}
        </div>
    `;
    
    resultsModal.show();
};

InteractiveReader.prototype.getScoreFeedback = function(score) {
    if (score >= 90) return "Excellent! You have outstanding reading comprehension.";
    if (score >= 80) return "Great job! Your reading comprehension is very good.";
    if (score >= 70) return "Good work! You understood most of the text well.";
    if (score >= 60) return "Not bad! Try reading more slowly and carefully next time.";
    return "Keep practicing! Focus on understanding the main ideas and key details.";
};

InteractiveReader.prototype.renderQuestionReview = function(results) {
    return this.comprehensionQuestions.map((q, i) => {
        const userAnswer = this.userAnswers[i];
        const isCorrect = userAnswer === q.correct_answer;
        
        return `
            <div class="card mb-2">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong>Q${i + 1}:</strong> ${q.question}
                        </div>
                        <span class="badge ${isCorrect ? 'bg-success' : 'bg-danger'} ms-2">
                            ${isCorrect ? '✓' : '✗'}
                        </span>
                    </div>
                    <div class="mt-2 small">
                        <div>Your answer: <span class="${isCorrect ? 'text-success' : 'text-danger'}">${userAnswer}</span></div>
                        ${!isCorrect ? `<div>Correct answer: <span class="text-success">${q.correct_answer}</span></div>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
};

InteractiveReader.prototype.selectNewArticle = function() {
    // Hide results modal if it's open
    const resultsModal = document.getElementById('resultsModal');
    if (resultsModal && bootstrap.Modal.getInstance(resultsModal)) {
        bootstrap.Modal.getInstance(resultsModal).hide();
    }
    
    // Hide questions modal if it's open
    const questionsModal = document.getElementById('questionsModal');
    if (questionsModal && bootstrap.Modal.getInstance(questionsModal)) {
        bootstrap.Modal.getInstance(questionsModal).hide();
    }
    
    // Reset reading state
    this.selectedMaterial = null;
    this.readingMode = null;
    this.currentSession = null;
    this.readingStartTime = null;
    this.vocabularyClicks = 0;
    this.wordsRead = 0;
    this.totalWords = 0;
    
    // Hide reading interface elements
    document.getElementById('readingHeader').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('readingModeSelection').style.display = 'none';
    
    // Reset reading controls
    document.getElementById('startReadingBtn').style.display = 'inline-block';
    document.getElementById('completeReadingBtn').style.display = 'none';
    
    // Reset interactive text area
    document.getElementById('interactiveText').innerHTML = `
        <div class="text-center text-muted">
            <i class="bi bi-book-half" style="font-size: 3rem;"></i>
            <p class="mt-3">Select a reading material from the sidebar to begin</p>
        </div>
    `;
    
    // Reset instructions to default
    const instructionsElement = document.getElementById('instructions');
    instructionsElement.innerHTML = `
        <h5><i class="bi bi-info-circle"></i> How to Use Interactive Reading</h5>
        <ul class="mb-0">
            <li><strong>Click on any word</strong> to see its definition, pronunciation, and examples</li>
            <li><strong>Double-click</strong> to get Chinese translation</li>
            <li><strong>Right-click on words</strong> to ask the AI chatbot for detailed explanations</li>
            <li><strong>Use the AI assistant</strong> (robot icon, bottom-right) for reading help and questions</li>
            <li><strong>Your reading speed</strong> and vocabulary learning are tracked automatically</li>
            <li><strong>Complete the reading</strong> to get comprehension questions and personalized feedback</li>
        </ul>
    `;
    instructionsElement.className = 'alert alert-info';
    instructionsElement.style.display = 'block';
    
    // Hide chatbot (will be shown again based on mode selection)
    document.getElementById('readingChatbot').style.display = 'none';
    
    // Clear material selection
    document.querySelectorAll('.material-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Reset progress bar
    const progressBar = document.getElementById('readingProgress');
    if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.textContent = '0% Complete';
    }
    
    // Reset reading stats display
    const readingTimeElement = document.getElementById('readingTime');
    const currentWPMElement = document.getElementById('currentWPM');
    if (readingTimeElement) readingTimeElement.textContent = '0:00';
    if (currentWPMElement) currentWPMElement.textContent = '0';
};

InteractiveReader.prototype.showReadingComplete = function() {
    // For AI mode, show colorful completion message
    this.showAICompletionModal();
};

InteractiveReader.prototype.showAICompletionModal = function() {
    // Create a beautiful completion modal for AI mode
    const completionHtml = `
        <div class="text-center">
            <div class="mb-4">
                <i class="bi bi-trophy-fill text-warning" style="font-size: 4rem;"></i>
            </div>
            <h2 class="text-success mb-3">🎉 Congratulations! 🎉</h2>
            <div class="alert alert-success border-0 shadow-sm mb-4">
                <h5 class="alert-heading mb-3">
                    <i class="bi bi-robot text-primary"></i> Reading Session Complete!
                </h5>
                <p class="mb-3">Great job completing your reading session with AI assistance!</p>
                <div class="row text-center">
                    <div class="col-md-4">
                        <div class="card border-0 bg-light">
                            <div class="card-body">
                                <i class="bi bi-clock-fill text-info mb-2" style="font-size: 1.5rem;"></i>
                                <h6>Reading Time</h6>
                                <p class="mb-0">${Math.round((Date.now() - this.readingStartTime) / 60000)} minutes</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-0 bg-light">
                            <div class="card-body">
                                <i class="bi bi-speedometer2 text-warning mb-2" style="font-size: 1.5rem;"></i>
                                <h6>Reading Speed</h6>
                                <p class="mb-0">${this.currentWPM} WPM</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-0 bg-light">
                            <div class="card-body">
                                <i class="bi bi-book-fill text-success mb-2" style="font-size: 1.5rem;"></i>
                                <h6>Words Explored</h6>
                                <p class="mb-0">${this.vocabularyClicks} words</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="alert alert-info border-0 shadow-sm mb-4">
                <h6><i class="bi bi-lightbulb-fill text-warning"></i> Learning Achievements</h6>
                <ul class="list-unstyled mb-0">
                    <li>✅ Successfully used AI assistance features</li>
                    <li>✅ Improved vocabulary through word exploration</li>
                    <li>✅ Enhanced reading comprehension skills</li>
                    <li>✅ Practiced English language learning</li>
                </ul>
            </div>
            <div class="d-grid gap-2">
                <button class="btn btn-primary btn-lg" id="readAnotherBtn">
                    <i class="bi bi-arrow-clockwise"></i> Read Another Article
                </button>
                <button class="btn btn-outline-secondary" id="returnToDashboardBtn">
                    <i class="bi bi-house"></i> Return to Dashboard
                </button>
            </div>
        </div>
    `;
    
    // Update or create the completion modal
    let modal = document.getElementById('aiCompletionModal');
    if (!modal) {
        // Create the modal if it doesn't exist
        modal = document.createElement('div');
        modal.id = 'aiCompletionModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content border-0 shadow">
                    <div class="modal-header bg-gradient" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <h5 class="modal-title">
                            <i class="bi bi-stars"></i> Reading Complete!
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4" id="aiCompletionContent">
                        <!-- Content will be populated here -->
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Update the content
    document.getElementById('aiCompletionContent').innerHTML = completionHtml;
    
    // Add event listeners for buttons
    setTimeout(() => {
        const readAnotherBtn = document.getElementById('readAnotherBtn');
        const returnToDashboardBtn = document.getElementById('returnToDashboardBtn');
        
        if (readAnotherBtn) {
            readAnotherBtn.addEventListener('click', () => {
                bootstrap.Modal.getInstance(modal).hide();
                this.selectNewArticle();
            });
        }
        
        if (returnToDashboardBtn) {
            returnToDashboardBtn.addEventListener('click', () => {
                bootstrap.Modal.getInstance(modal).hide();
            });
        }
    }, 100);
    
    // Show the modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
};

// Initialize the interactive reader when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new InteractiveReader();
});