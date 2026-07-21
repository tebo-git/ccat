export interface Question {
  uid: string;
  id: number;
  category: string;
  difficulty: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface TestResponse {
  count: number;
  questions: Question[];
}

export type Screen = 'landing' | 'test' | 'results';
