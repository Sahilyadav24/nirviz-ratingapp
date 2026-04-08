interface Props {
  onRegister: () => void;
}

export default function ReviewPrompt({ onRegister }: Props) {
  const googleReviewUrl = process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL || "#";

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <div className="text-5xl">⭐</div>

      <div>
        <h2 className="text-xl font-bold text-brand-dark">Enjoyed your visit?</h2>
        <p className="text-sm text-gray-500 mt-1">
          Leave us a Google review — it takes just 30 seconds!
        </p>
      </div>

      {/* Step 1 */}
      <div className="w-full flex flex-col gap-2">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Step 1</p>
        <a
          href={googleReviewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full bg-brand text-white font-semibold py-3 rounded-xl text-base active:scale-95 transition-transform block"
        >
          Leave a Google Review ⭐
        </a>
      </div>

      {/* Divider */}
      <div className="w-full flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-xs text-gray-400">then</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* Step 2 */}
      <div className="w-full flex flex-col gap-2">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Step 2</p>
        <button
          onClick={onRegister}
          className="w-full bg-white border-2 border-brand text-brand font-semibold py-3 rounded-xl text-base active:scale-95 transition-transform"
        >
          I've left a review → Register &amp; Win
        </button>
      </div>

      <p className="text-xs text-gray-400">
        Register your details for a chance to win an exciting prize!
      </p>
    </div>
  );
}
