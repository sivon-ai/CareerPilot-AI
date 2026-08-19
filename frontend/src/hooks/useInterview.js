import { useCallback, useMemo, useState } from 'react';

import { startInterview, submitInterviewAnswer, getInterviewReport, getFriendlyApiError } from '../services/api';

export const useInterview = () => {
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(10);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [completed, setCompleted] = useState(false);

  const reset = useCallback(() => {
    setSession(null);
    setCurrentQuestion(null);
    setQuestionNumber(1);
    setTotalQuestions(10);
    setAnswer('');
    setEvaluation(null);
    setCompleted(false);
    setError('');
  }, []);

  const start = useCallback(async ({ resumeDocumentId, jobDocumentId, interviewType = 'mixed', difficulty = 'medium', questionCount = 10 }) => {
    setLoading(true);
    setError('');
    setCompleted(false);

    try {
      const payload = await startInterview({
        resume_document_id: resumeDocumentId,
        job_document_id: jobDocumentId,
        interview_type: interviewType,
        difficulty,
        question_count: questionCount,
      });

      setSession(payload.session_id ? { session_id: payload.session_id } : null);
      setCurrentQuestion(payload.question || null);
      setQuestionNumber(payload.question_number || 1);
      setTotalQuestions(payload.total_questions || questionCount);
      setAnswer('');
      setEvaluation(null);
      return payload;
    } catch (startError) {
      setError(getFriendlyApiError(startError));
      throw startError;
    } finally {
      setLoading(false);
    }
  }, []);

  const submitAnswer = useCallback(async () => {
    if (!session?.session_id || !currentQuestion?.id || !answer.trim()) {
      throw new Error('Please enter an answer before submitting.');
    }

    setSubmitting(true);
    setError('');

    try {
      const payload = await submitInterviewAnswer(session.session_id, {
        question_id: currentQuestion.id,
        answer,
      });

      setEvaluation(payload.evaluation || null);
      setCurrentQuestion(payload.next_question || null);
      setCompleted(Boolean(payload.completed));
      setAnswer('');
      if (payload.next_question) {
        setQuestionNumber((current) => current + 1);
      }
      return payload;
    } catch (submitError) {
      setError(getFriendlyApiError(submitError));
      throw submitError;
    } finally {
      setSubmitting(false);
    }
  }, [answer, currentQuestion, session]);

  const report = useMemo(() => ({
    hasSession: Boolean(session?.session_id),
    canSubmit: Boolean(session?.session_id && currentQuestion?.id && answer.trim() && !submitting),
  }), [answer, currentQuestion, session, submitting]);

  return {
    session,
    currentQuestion,
    questionNumber,
    totalQuestions,
    answer,
    setAnswer,
    evaluation,
    loading,
    submitting,
    error,
    completed,
    start,
    submitAnswer,
    reset,
    report,
  };
};
