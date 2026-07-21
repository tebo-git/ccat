export type Screen = 'landing' | 'test' | 'results';

export interface Question {
  uid: string;
  id: number;
  category: string;
  difficulty: string;
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  type?: string;
  sequence_images?: string[];
  option_images?: string[];
}

export interface TestResponse {
  count: number;
  questions: Question[];
}