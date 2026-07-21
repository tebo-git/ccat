import { useState, useEffect, useCallback, useRef } from 'react';
import { Timer, CheckCircle, XCircle, Brain, ArrowRight, Play, Clock, BarChart3, ChevronRight, ChevronLeft, Award } from 'lucide-react';
import type { Question, TestResponse, Screen } from './types';

const TOTAL_QUESTIONS = 50;
const TEST_DURATION_SECONDS = 15 * 60;

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
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/test?count=${TOTAL_QUESTIONS}`);
      if (!res.ok) throw new Error('Failed to fetch questions');
      const data: TestResponse = await res.json();
      setQuestions(data.questions);
      setAnswers({});
      setCurrentIndex(0);
      setTimeLeft(TEST_DURATION_SECONDS);
      setScreen('test');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const finishTest = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setScreen('results');
  }, []);

  useEffect(() => {
    if (screen === 'test') {
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            finishTest();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
  }, [screen, finishTest]);

  const handleAnswer = (option: string) => {
    setAnswers((prev) => ({ ...prev, [questions[currentIndex].uid]: option }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      finishTest();
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const results = questions.map((q) => {
    const selected = answers[q.uid] || null;
    const isCorrect = selected === q.correct_answer;
    return { question: q, selected, isCorrect };
  });

  const correctCount = results.filter((r) => r.isCorrect).length;
  const incorrectCount = results.filter((r) => r.selected !== null && !r.isCorrect).length;
  const unansweredCount = TOTAL_QUESTIONS - correctCount - incorrectCount;
  const percentage = Math.round((correctCount / TOTAL_QUESTIONS) * 100);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {screen === 'landing' && (
        <LandingScreen onStart={startTest} loading={loading} error={error} />
      )}
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

function LandingScreen({
  onStart,
  loading,
  error,
}: {
  onStart: () => void;
  loading: boolean;
  error: string | null;
}) {
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
          Assess your verbal and numerical reasoning skills with this comprehensive aptitude test.
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
            <div className="text-2xl font-bold text-slate-900">2</div>
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
              <span>Timer runs continuously — you cannot pause. Answer all questions before time runs out.</span>
            </li>
          </ul>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 rounded-xl p-4 mb-6 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={onStart}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-xl text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Loading...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Test
            </>
          )}
        </button>
      </div>
    </div>
  );
}

function TestScreen({
  questions,
  currentIndex,
  answers,
  timeLeft,
  onAnswer,
  onNext,
  onPrevious,
  onFinish,
}: {
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

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-slate-900 text-sm hidden sm:inline">CCAT Aptitude Test</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-slate-100 rounded-lg px-3 py-1.5">
              <span className="text-xs text-slate-500 font-medium">Question</span>
              <span className="text-sm font-bold text-slate-900">
                {currentIndex + 1} / {questions.length}
              </span>
            </div>
            <div
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-sm font-bold ${
                isDanger
                  ? 'bg-red-50 text-red-600'
                  : isWarning
                    ? 'bg-amber-50 text-amber-600'
                    : 'bg-blue-50 text-blue-600'
              }`}
            >
              <Timer className="w-4 h-4" />
              {formatTime(timeLeft)}
            </div>
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-slate-100">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
          />
        </div>
      </header>

      {/* Question */}
      <main className="flex-1 flex flex-col items-center px-4 py-8">
        <div className="w-full max-w-2xl">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <div className="flex items-center gap-2 mb-6">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700">
                {q.category}
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
                {q.difficulty}
              </span>
            </div>

            <h2 className="text-lg sm:text-xl font-semibold text-slate-900 mb-6 leading-relaxed">
              {q.question}
            </h2>

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
                      <span
                        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold shrink-0 ${
                          isSelected
                            ? 'border-blue-600 bg-blue-600 text-white'
                            : 'border-slate-300 text-slate-400'
                        }`}
                      >
                        {String.fromCharCode(65 + idx)}
                      </span>
                      {option}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Navigation */}
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
              <button
                onClick={onFinish}
                className="px-4 py-2.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 bg-white hover:bg-slate-50 hover:text-slate-900 transition-colors"
              >
                Finish
              </button>
              <button
                onClick={onNext}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
              >
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

function ResultsScreen({
  results,
  correctCount,
  incorrectCount,
  unansweredCount,
  percentage,
  onRestart,
}: {
  results: { question: Question; selected: string | null; isCorrect: boolean }[];
  correctCount: number;
  incorrectCount: number;
  unansweredCount: number;
  percentage: number;
  onRestart: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-slate-900">CCAT Aptitude Test</span>
          </div>
          <button
            onClick={onRestart}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <ArrowRight className="w-4 h-4" />
            New Test
          </button>
        </div>
      </header>

      <main className="flex-1 px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Score Summary */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-6 text-center">Test Results</h2>

            <div className="flex items-center justify-center mb-8">
              <div className="relative w-40 h-40">
                <svg className="w-40 h-40 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${percentage * 2.64} 264`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold text-slate-900">{percentage}%</span>
                  <span className="text-sm text-slate-500">{correctCount} / {results.length}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-emerald-50 rounded-lg">
                <div className="flex items-center justify-center mb-1">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="text-xl font-bold text-emerald-700">{correctCount}</div>
                <div className="text-xs text-emerald-600">Correct</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="flex items-center justify-center mb-1">
                  <XCircle className="w-5 h-5 text-red-600" />
                </div>
                <div className="text-xl font-bold text-red-700">{incorrectCount}</div>
                <div className="text-xs text-red-600">Incorrect</div>
              </div>
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-center mb-1">
                  <Clock className="w-5 h-5 text-slate-500" />
                </div>
                <div className="text-xl font-bold text-slate-700">{unansweredCount}</div>
                <div className="text-xs text-slate-500">Unanswered</div>
              </div>
            </div>
          </div>

          {/* Breakdown */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Question Breakdown</h3>
            <div className="space-y-4">
              {results.map((r, idx) => (
                <div
                  key={r.question.uid}
                  className="border border-slate-100 rounded-lg p-4 hover:border-slate-200 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="shrink-0 mt-0.5">
                      {r.isCorrect ? (
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                      ) : r.selected ? (
                        <XCircle className="w-5 h-5 text-red-600" />
                      ) : (
                        <Clock className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-slate-400">Q{idx + 1}</span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                          {r.question.category}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-900 mb-2">{r.question.question}</p>
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
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
