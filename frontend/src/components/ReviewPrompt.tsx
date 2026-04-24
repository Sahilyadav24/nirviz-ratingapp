interface Props {
  onRegister: () => void;
}

export default function ReviewPrompt({ onRegister }: Props) {
  const googleReviewUrl = process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL || "#";

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <div className="text-6xl">🎁</div>

      <div>
        <h2 className="text-2xl font-bold text-brand-dark">Register &amp; Win!</h2>
        <p className="text-gray-500 mt-1 text-sm">
          Fill in your details for a chance to win an exciting prize!
        </p>
      </div>

      {/* Primary CTA — Register & Win */}
      <button
        onClick={onRegister}
        className="w-full bg-brand text-white font-bold py-4 rounded-xl text-lg active:scale-95 transition-transform shadow-lg shadow-brand/30"
      >
        Register &amp; Win a Prize 🎉
      </button>

      {/* Divider */}
      <div className="w-full flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-xs text-gray-400">also</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* Secondary CTA — Google Review */}
      <div className="w-full flex flex-col gap-2">
        <p className="text-xs text-gray-500">Enjoyed your visit? Leave us a quick review!</p>
        <a
          href={googleReviewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full bg-gray-50 border border-gray-200 text-gray-600 font-medium py-2.5 rounded-xl text-sm active:scale-95 transition-transform block"
        >
          Leave a Google Review ⭐
        </a>
      </div>
    </div>
  );
}
