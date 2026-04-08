import { useRef, useState } from "react";
import axios from "axios";

const extractError = (err: any, fallback: string): string => {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: any) => d.msg).join(", ");
  return fallback;
};

interface Props {
  phone: string;
  email: string;
  onVerified: (sessionToken: string) => void;
  onBack: () => void;
}

export default function OtpInput({ phone, email, onVerified, onBack }: Props) {
  const [otp, setOtp] = useState<string[]>(Array(6).fill(""));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const updated = [...otp];
    updated[index] = value.slice(-1);
    setOtp(updated);
    if (value && index < 5) inputs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(""));
      inputs.current[5]?.focus();
    }
  };

  const handleVerify = async () => {
    const otpString = otp.join("");
    if (otpString.length < 6) { setError("Enter all 6 digits"); return; }
    setError("");
    setLoading(true);
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/otp/verify`, {
        phone,
        email,
        otp: otpString,
      });
      onVerified(res.data.session_token);
    } catch (err: any) {
      setError(extractError(err, "Invalid OTP. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/otp/send`, { phone, email });
      setResendCooldown(30);
      const interval = setInterval(() => {
        setResendCooldown((c) => { if (c <= 1) { clearInterval(interval); return 0; } return c - 1; });
      }, 1000);
    } catch (err: any) {
      setError(extractError(err, "Could not resend OTP."));
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-brand-dark">Verify OTP</h2>
        <p className="text-sm text-gray-500 mt-1">
          OTP sent to: <span className="font-medium">{email}</span>
        </p>
      </div>

      {/* 6-digit OTP boxes */}
      <div className="flex justify-center gap-2" onPaste={handlePaste}>
        {otp.map((digit, i) => (
          <input
            key={i}
            ref={(el) => { inputs.current[i] = el; }}
            className="otp-box"
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            autoFocus={i === 0}
          />
        ))}
      </div>

      {error && <p className="text-red-500 text-sm text-center">{error}</p>}

      <button
        onClick={handleVerify}
        disabled={loading}
        className="bg-brand text-white font-semibold py-3 rounded-xl text-base active:scale-95 transition-transform disabled:opacity-60"
      >
        {loading ? "Verifying..." : "Verify & Continue"}
      </button>

      <div className="flex justify-between text-sm text-gray-500">
        <button onClick={onBack} className="underline">Change number</button>
        <button
          onClick={handleResend}
          disabled={resendCooldown > 0}
          className="underline disabled:no-underline disabled:text-gray-400"
        >
          {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend OTP"}
        </button>
      </div>
    </div>
  );
}
