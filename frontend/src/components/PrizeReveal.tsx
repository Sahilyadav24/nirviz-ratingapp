import { useEffect, useRef, useState } from "react";
import axios from "axios";

const extractError = (err: any, fallback: string): string => {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: any) => d.msg).join(", ");
  return fallback;
};

interface Props {
  formData: { name: string; phone: string; address: string };
  sessionToken: string;
  prize: { prize_name: string; prize_description: string; customer_id: string } | null;
  onRegistered: (prize: { prize_name: string; prize_description: string; customer_id: string }) => void;
}

export default function PrizeReveal({ formData, sessionToken, prize, onRegistered }: Props) {
  const [loading, setLoading] = useState(!prize);
  const [error, setError] = useState("");
  const [revealed, setRevealed] = useState(false);
  const registered = useRef(false);

  useEffect(() => {
    if (prize) return;
    if (registered.current) return;
    registered.current = true;
    const register = async () => {
      try {
        const res = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/customer/register`,
          { ...formData, session_token: sessionToken }
        );
        const prizeRes = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/prize/${res.data.customer_id}`
        );
        onRegistered({ ...prizeRes.data, customer_id: res.data.customer_id });
      } catch (err: any) {
        setError(extractError(err, "Something went wrong. Please contact staff."));
      } finally {
        setLoading(false);
        setTimeout(() => setRevealed(true), 300);
      }
    };
    register();
  }, []);

  useEffect(() => {
    if (prize) setTimeout(() => setRevealed(true), 300);
  }, [prize]);

  const googleReviewUrl = process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL || "#";

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-500 text-sm">Registering your entry...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <p className="text-red-500 font-medium">{error}</p>
        <p className="text-sm text-gray-400 mt-2">Please show this to our staff.</p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center gap-5 text-center transition-all duration-500 ${
        revealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
    >
      <div className="text-5xl">🎉</div>
      <h2 className="text-2xl font-bold text-brand-dark">Congratulations!</h2>
      <p className="text-gray-600 text-sm">
        Hi <span className="font-semibold">{formData.name}</span>, you&apos;ve won:
      </p>

      <div className="w-full bg-brand-light border border-brand/30 rounded-xl px-5 py-4">
        <p className="text-xl font-bold text-brand-dark">{prize?.prize_name}</p>
        <p className="text-sm text-gray-600 mt-1">{prize?.prize_description}</p>
      </div>

      <p className="text-xs text-gray-400">
        A confirmation has been sent to your mobile.
      </p>

      <a
        href={googleReviewUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full bg-brand text-white font-semibold py-3 rounded-xl text-base text-center active:scale-95 transition-transform block"
      >
        Leave Us a Review ⭐
      </a>
    </div>
  );
}
