import { useState, useEffect, useCallback, useRef } from 'react';
import { Timer, CheckCircle, XCircle, Brain, ArrowRight, Play, Clock, BarChart3, ChevronRight, ChevronLeft, Award } from 'lucide-react';
import type { Question, TestResponse, Screen } from './types';

import verbalBank from './data/verbal_bank.json';
import numericalBank from './data/numerical_bank.json';
import abstractBank from './data/abstract_bank.json';

const TOTAL_QUESTIONS = 50;
const TEST_DURATION_SECONDS = 15 * 60;
const API_BASE = 'https://ccat-backend-api.onrender.com';
// const API_BASE = 'http://127.0.0.1:8000';

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function App() {
  const [screen, setScreen] = useState<Screen>('landing');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [timeLeft, setTimeLeft] = useState(TEST_DURATION_SECONDS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLockModal, setShowLockModal] = useState(false);
  const [licenseKey, setLicenseKey] = useState('');
  const [licenseLoading, setLicenseLoading] = useState(false);
  const [licenseError, setLicenseError] = useState<string | null>(null);
  const [isUnlocked, setIsUnlocked] = useState(() => {
    return localStorage.getItem('ccat_unlocked') === 'true';
  });
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const getQuestionsForTest = (testNum: number): Question[] => {
    const verbal = verbalBank as Question[];
    const numerical = numericalBank as Question[];
    const abstract = abstractBank as Question[];

    // Fix image paths for abstract questions to use local public folder
    const fixedAbstract = abstract.map(q => ({
      ...q,
      uid: `a-${q.id}`,
      sequence_images: q.sequence_images?.map((p: string) => `/abstract_images/${p.split('/').pop()}`) || [],
      option_images: q.option_images?.map((p: string) => `/abstract_images/${p.split('/').pop()}`) || [],
    }));

    // Add uids to verbal and numerical
    const taggedVerbal = verbal.map(q => ({ ...q, uid: `v-${q.id}` }));
    const taggedNumerical = numerical.map(q => ({ ...q, uid: `n-${q.id}` }));

    const chunkSize = Math.floor(verbal.length / 3);
    const start = (testNum - 1) * chunkSize;
    const end = start + chunkSize;

    const vPool = taggedVerbal.slice(start, end);
    const nPool = taggedNumerical.slice(start, end);
    const aPool = fixedAbstract.slice(start, end);

    const combined = [...vPool, ...nPool, ...aPool];
    // Shuffle
    for (let i = combined.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [combined[i], combined[j]] = [combined[j], combined[i]];
    }
    return combined.slice(0, TOTAL_QUESTIONS);
  };

  const startTest = async (testNum: number = 1) => {
    if ((testNum === 2 || testNum === 3) && !isUnlocked) {
      setShowLockModal(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const questions = getQuestionsForTest(testNum);
      setQuestions(questions);
      setAnswers({});
      setCurrentIndex(0);
      setTimeLeft(TEST_DURATION_SECONDS);
      setScreen('test');
      fetch(`${API_BASE}/`).catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const validateLicense = async () => {
    if (!licenseKey.trim()) {
      setLicenseError('Please enter a license key');
      return;
    }
    setLicenseLoading(true);
    setLicenseError(null);
    try {
      const res = await fetch(`${API_BASE}/api/verify-license`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey.trim() })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('ccat_unlocked', 'true');
        setIsUnlocked(true);
        setShowLockModal(false);
        setLicenseError(null);
      } else {
        setLicenseError('Invalid license key. Please check and try again.');
      }
    } catch (e) {
      setLicenseError('Could not verify license. Please try again.');
    } finally {
      setLicenseLoading(false);
    }
  };

  const finishTest = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setScreen('results');
  }, []);

  useEffect(() => {
    if (screen === 'test' && timerRef.current === null) {
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            if (timerRef.current) {
              clearInterval(timerRef.current);
              timerRef.current = null;
            }
            setScreen('results');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (screen !== 'test' && timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [screen]);

  const handleAnswer = (option: string) => {
    setAnswers((prev) => ({ ...prev, [questions[currentIndex].uid]: option }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) setCurrentIndex((prev) => prev + 1);
    else finishTest();
  };

  const handlePrevious = () => {
    if (currentIndex > 0) setCurrentIndex((prev) => prev - 1);
  };

  const results = questions.map((q) => {
    const selected = answers[q.uid] || null;
    return { question: q, selected, isCorrect: selected === q.correct_answer };
  });

  const correctCount = results.filter((r) => r.isCorrect).length;
  const incorrectCount = results.filter((r) => r.selected !== null && !r.isCorrect).length;
  const unansweredCount = TOTAL_QUESTIONS - correctCount - incorrectCount;
  const percentage = Math.round((correctCount / TOTAL_QUESTIONS) * 100);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">

      {showLockModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 text-center">
            <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Unlock Full Access</h2>
            <p className="text-slate-600 text-sm mb-4">Get two more full-length CCAT practice tests with:</p>
            <ul className="text-sm text-slate-600 text-left space-y-2 mb-6 bg-slate-50 rounded-xl p-4">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                50 unique questions per test
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                Verbal, numerical and abstract reasoning
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                Detailed PDF results with improvement tips
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                Full answer explanations
              </li>
            </ul>
            <a
              href="https://8396304264007.gumroad.com/l/eakpb"
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors mb-4"
            >
              Unlock 2 More Tests — $25
            </a>

            <div className="border-t border-slate-100 pt-4 mt-2">
              <p className="text-xs text-slate-500 mb-2">Already purchased? Enter your license key:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  placeholder="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX"
                  className="flex-1 px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={validateLicense}
                  disabled={licenseLoading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                >
                  {licenseLoading ? '...' : 'Unlock'}
                </button>
              </div>
              {licenseError && <p className="text-red-600 text-xs mt-1">{licenseError}</p>}
            </div>

            <button
              onClick={() => setShowLockModal(false)}
              className="text-sm text-slate-500 hover:text-slate-700 transition-colors mt-3"
            >
              Maybe later
            </button>
          </div>
        </div>
      )}

      {screen === 'landing' && <LandingScreen onStart={startTest} loading={loading} error={error} />}
      {screen === 'test' && (
        <TestScreen
          questions={questions}
          currentIndex={currentIndex}
          answers={answers}
          timeLeft={timeLeft}
          onAnswer={handleAnswer}
          onNext={handleNext}
          onPrevious={handlePrevious}
          onFinish={finishTest}
        />
      )}
      {screen === 'results' && (
        <ResultsScreen
          results={results}
          correctCount={correctCount}
          incorrectCount={incorrectCount}
          unansweredCount={unansweredCount}
          percentage={percentage}
          onRestart={() => setScreen('landing')}
        />
      )}
    </div>
  );
}

function LandingScreen({ onStart, loading, error }: { onStart: (testNum: number) => void; loading: boolean; error: string | null }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="max-w-2xl w-full text-center">
        <div className="mb-8 flex justify-center">
          <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
            <Brain className="w-10 h-10 text-white" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-3">CCAT Aptitude Test</h1>
        <p className="text-lg text-slate-600 mb-10">
          Assess your verbal, numerical and abstract reasoning skills with this comprehensive aptitude test.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-center mb-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">50</div>
            <div className="text-sm text-slate-500">Questions</div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-center mb-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">15</div>
            <div className="text-sm text-slate-500">Minutes</div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-center mb-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <Award className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">3</div>
            <div className="text-sm text-slate-500">Categories</div>
          </div>
        </div>
        <div className="bg-blue-50 rounded-xl p-5 mb-10 text-left">
          <h3 className="font-semibold text-blue-900 mb-2">Test Overview</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <span>Verbal reasoning — evaluate arguments, identify assumptions, and draw conclusions.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <span>Numerical reasoning — interpret data, solve word problems, and calculate percentages.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <span>Abstract reasoning — identify patterns, complete sequences, and solve visual matrices.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <span>Timer runs continuously — you cannot pause. Answer all questions before time runs out.</span>
            </li>

            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <span>No calculator allowed — all numerical questions are designed to be solved mentally.</span>
            </li>
          </ul>
        </div>
        {error && <div className="bg-red-50 text-red-700 rounded-xl p-4 mb-6 text-sm">{error}</div>}
        <div className="space-y-3">
          <p className="text-sm text-slate-500 font-medium">Choose a practice test:</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={() => onStart(1)}
              disabled={loading}
              className="flex flex-col items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-4 rounded-xl transition-colors disabled:opacity-50 shadow-sm"
            >
              <Play className="w-5 h-5" />
              <span>Test 1</span>
              <span className="text-xs font-normal opacity-80">Free</span>
            </button>
            <button
              onClick={() => onStart(2)}
              disabled={loading}
              className="flex flex-col items-center gap-1 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-6 py-4 rounded-xl border border-slate-200 transition-colors disabled:opacity-50 shadow-sm"
            >
              <Play className="w-5 h-5" />
              <span>Test 2</span>
              <span className="text-xs font-normal text-slate-400">Full Practice</span>
            </button>
            <button
              onClick={() => onStart(3)}
              disabled={loading}
              className="flex flex-col items-center gap-1 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-6 py-4 rounded-xl border border-slate-200 transition-colors disabled:opacity-50 shadow-sm"
            >
              <Play className="w-5 h-5" />
              <span>Test 3</span>
              <span className="text-xs font-normal text-slate-400">Full Practice</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Abstract question renderer
function AbstractQuestion({ q, selected, onAnswer }: { q: Question; selected: string | null; onAnswer: (opt: string) => void }) {
  const optionLabels = ['A', 'B', 'C', 'D', 'E'];

  return (
    <div>
      {/* Show sequence images if present */}
      {q.sequence_images && q.sequence_images.length > 0 && (
        <div className="mb-6">
          <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wide">
            {q.type === 'matrix_3x3' ? 'Complete the matrix:' : 'What comes next in the series?'}
          </p>
          <div className={`grid gap-2 ${q.type === 'matrix_3x3' ? 'grid-cols-3' : 'grid-cols-4'}`}>
            {q.sequence_images.map((src, i) => (
              <div key={i} className="border border-slate-200 rounded-lg bg-white p-1 flex items-center justify-center">
                <img src={src} alt={`Step ${i + 1}`} className="w-16 h-16 sm:w-20 sm:h-20" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Show image options */}
      <p className="text-xs text-slate-500 mb-3 font-medium uppercase tracking-wide">Choose your answer:</p>
      <div className="grid grid-cols-5 gap-2">
        {q.option_images.map((src, idx) => {
          const label = optionLabels[idx];
          const isSelected = selected === label;
          return (
            <button
              key={idx}
              onClick={() => onAnswer(label)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg border-2 transition-all ${
                isSelected
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-slate-200 bg-white hover:border-blue-300'
              }`}
            >
              <img src={src} alt={`Option ${label}`} className="w-14 h-14 sm:w-16 sm:h-16" />
              <span className={`text-xs font-bold ${isSelected ? 'text-blue-700' : 'text-slate-500'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function TestScreen({ questions, currentIndex, answers, timeLeft, onAnswer, onNext, onPrevious, onFinish }: {
  questions: Question[];
  currentIndex: number;
  answers: Record<string, string>;
  timeLeft: number;
  onAnswer: (option: string) => void;
  onNext: () => void;
  onPrevious: () => void;
  onFinish: () => void;
}) {
  const q = questions[currentIndex];
  const selected = answers[q.uid] || null;
  const isLast = currentIndex === questions.length - 1;
  const isWarning = timeLeft <= 60;
  const isDanger = timeLeft <= 30;
  const isAbstract = q.category === 'abstract';

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-slate-900 text-sm hidden sm:inline">CCAT Aptitude Test</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-slate-100 rounded-lg px-3 py-1.5">
              <span className="text-xs text-slate-500 font-medium">Question</span>
              <span className="text-sm font-bold text-slate-900">{currentIndex + 1} / {questions.length}</span>
            </div>
            <div className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-sm font-bold ${
              isDanger ? 'bg-red-50 text-red-600' : isWarning ? 'bg-amber-50 text-amber-600' : 'bg-blue-50 text-blue-600'
            }`}>
              <Timer className="w-4 h-4" />
              {formatTime(timeLeft)}
            </div>
          </div>
        </div>
        <div className="h-1 bg-slate-100">
          <div className="h-full bg-blue-600 transition-all duration-300" style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }} />
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center px-4 py-8">
        <div className="w-full max-w-2xl">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <h2 className="text-lg sm:text-xl font-semibold text-slate-900 mb-6 leading-relaxed">
              {q.question}
            </h2>

            {isAbstract ? (
              <AbstractQuestion q={q} selected={selected} onAnswer={onAnswer} />
            ) : (
              <div className="space-y-3">
                {q.options.map((option, idx) => {
                  const isSelected = selected === option;
                  return (
                    <button
                      key={idx}
                      onClick={() => onAnswer(option)}
                      className={`w-full text-left px-5 py-4 rounded-lg border text-sm sm:text-base font-medium transition-all duration-150 ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50 text-blue-900 ring-1 ring-blue-600'
                          : 'border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:bg-blue-50/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold shrink-0 ${
                          isSelected ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 text-slate-400'
                        }`}>
                          {String.fromCharCode(65 + idx)}
                        </span>
                        {option}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between mt-6">
            <button
              onClick={onPrevious}
              disabled={currentIndex === 0}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <div className="flex items-center gap-2">
              <button onClick={onFinish} className="px-4 py-2.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 bg-white hover:bg-slate-50 transition-colors">
                Finish
              </button>
              <button onClick={onNext} className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm">
                {isLast ? 'Finish' : 'Next'}
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ResultsScreen({ results, correctCount, incorrectCount, unansweredCount, percentage, onRestart }: {
  results: { question: Question; selected: string | null; isCorrect: boolean }[];
  correctCount: number;
  incorrectCount: number;
  unansweredCount: number;
  percentage: number;
  onRestart: () => void;
}) {
  const [email, setEmail] = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);

  const sendResults = async () => {
    if (!email || !email.includes('@')) {
      setEmailError('Please enter a valid email address');
      return;
    }
    setEmailLoading(true);
    setEmailError(null);
    try {
      const payload = {
        email,
        score: correctCount,
        total: results.length,
        percentage,
        results: results.map(r => ({
          question: r.question.question,
          category: r.question.category,
          selected: r.selected,
          correct_answer: r.question.correct_answer,
          is_correct: r.isCorrect,
          explanation: r.question.explanation || ''
        }))
      };
      const res = await fetch(`${API_BASE}/api/send-results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        setEmailSent(true);
      } else {
        setEmailError(data.message || 'Failed to send email');
      }
    } catch (e) {
      setEmailError('Failed to send email. Please try again.');
    } finally {
      setEmailLoading(false);
    }
  };




  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-slate-900">CCAT Aptitude Test</span>
          </div>
          <button onClick={onRestart} className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors">
            <ArrowRight className="w-4 h-4" />
            New Test
          </button>
        </div>
      </header>

      <main className="flex-1 px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">

          {!emailSent ? (
            /* Email gate -- shown before email submitted */
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
              <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Test Complete!</h2>
              <p className="text-slate-600 mb-8">Enter your email to see your full results, score breakdown, and correct answers.</p>

              <div className="max-w-md mx-auto">
                <div className="flex gap-2 mb-3">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendResults()}
                    placeholder="your@email.com"
                    className="flex-1 px-4 py-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={sendResults}
                    disabled={emailLoading}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50"
                  >
                    {emailLoading ? 'Sending...' : 'See Results'}
                  </button>
                </div>
                {emailLoading && (
  <p className="text-xs text-amber-600 mt-2">⏳ Processing your results, please wait up to 60 seconds...</p>)}
                {emailError && <p className="text-red-600 text-xs mt-2">{emailError}</p>}
                <p className="text-xs text-slate-400 mt-3">We'll also email you a copy of your results. This may take up to 60 seconds.</p>
              </div>
            </div>
          ) : (
            /* Results shown after email submitted */
            <>
              {/* Score Summary */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
                <h2 className="text-2xl font-bold text-slate-900 mb-6 text-center">Your Results</h2>
                <div className="flex items-center justify-center mb-8">
                  <div className="relative w-40 h-40">
                    <svg className="w-40 h-40 -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                      <circle cx="50" cy="50" r="42" fill="none" stroke="#2563eb" strokeWidth="8" strokeLinecap="round" strokeDasharray={`${percentage * 2.64} 264`} />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-3xl font-bold text-slate-900">{percentage}%</span>
                      <span className="text-sm text-slate-500">{correctCount} / {results.length}</span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-emerald-50 rounded-lg">
                    <div className="flex items-center justify-center mb-1"><CheckCircle className="w-5 h-5 text-emerald-600" /></div>
                    <div className="text-xl font-bold text-emerald-700">{correctCount}</div>
                    <div className="text-xs text-emerald-600">Correct</div>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <div className="flex items-center justify-center mb-1"><XCircle className="w-5 h-5 text-red-600" /></div>
                    <div className="text-xl font-bold text-red-700">{incorrectCount}</div>
                    <div className="text-xs text-red-600">Incorrect</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-center mb-1"><Clock className="w-5 h-5 text-slate-500" /></div>
                    <div className="text-xl font-bold text-slate-700">{unansweredCount}</div>
                    <div className="text-xs text-slate-500">Unanswered</div>
                  </div>
                </div>
              </div>

              {/* Email sent confirmation */}
              <div className="bg-emerald-50 rounded-xl border border-emerald-100 p-4 flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                <p className="text-sm text-emerald-800">Results sent to <strong>{email}</strong>. Check your inbox for your full breakdown.</p>
              </div>

              {/* Upsell */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 text-center">
                <h3 className="font-bold text-slate-900 mb-2">Want more practice?</h3>
                <p className="text-sm text-slate-600 mb-4">Get two more full-length practice tests with detailed PDF results for just $25.</p>
                <a
                  href="https://8396304264007.gumroad.com/l/eakpb"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
                >
                  Unlock 2 More Tests — $25
                </a>
              </div>

              {/* Question Breakdown */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
                <h3 className="text-lg font-bold text-slate-900 mb-4">Question Breakdown</h3>
                <div className="space-y-4">
                  {results.map((r, idx) => (
                    <div key={r.question.uid} className="border border-slate-100 rounded-lg p-4 hover:border-slate-200 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className="shrink-0 mt-0.5">
                          {r.isCorrect ? <CheckCircle className="w-5 h-5 text-emerald-600" /> : r.selected ? <XCircle className="w-5 h-5 text-red-600" /> : <Clock className="w-5 h-5 text-slate-400" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-slate-400">Q{idx + 1}</span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">{r.question.category}</span>
                          </div>
                          <p className="text-sm font-medium text-slate-900 mb-2">{r.question.question}</p>
                          {r.question.category === 'abstract' ? (
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center gap-2">
                                <span className="text-slate-500 w-24 shrink-0">Your answer:</span>
                                <span className={r.isCorrect ? 'text-emerald-700 font-medium' : r.selected ? 'text-red-700 font-medium' : 'text-slate-400 italic'}>
                                  {r.selected ? `Option ${r.selected}` : 'Not answered'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-slate-500 w-24 shrink-0">Correct:</span>
                                <span className="text-emerald-700 font-medium">Option {r.question.correct_answer}</span>
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-slate-500 w-24 shrink-0">Explanation:</span>
                                <span className="text-slate-600 text-xs">{r.question.explanation}</span>
                              </div>
                            </div>
                          ) : (
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center gap-2">
                                <span className="text-slate-500 w-20 shrink-0">Your answer:</span>
                                <span className={r.isCorrect ? 'text-emerald-700 font-medium' : r.selected ? 'text-red-700 font-medium' : 'text-slate-400 italic'}>
                                  {r.selected || 'Not answered'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-slate-500 w-20 shrink-0">Correct:</span>
                                <span className="text-emerald-700 font-medium">{r.question.correct_answer}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

        </div>
      </main>
    </div>
  );
}

export default App;