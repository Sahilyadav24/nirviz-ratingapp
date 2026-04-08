import { useState } from "react";
import Head from "next/head";
import ReviewPrompt from "@/components/ReviewPrompt";
import CustomerForm from "@/components/CustomerForm";
import OtpInput from "@/components/OtpInput";
import PrizeReveal from "@/components/PrizeReveal";

type Step = "landing" | "form" | "otp" | "prize";

interface FormData {
  name: string;
  phone: string;
  email: string;
  address: string;
}

interface PrizeData {
  prize_name: string;
  prize_description: string;
  customer_id: string;
}

export default function Home() {
  const [step, setStep] = useState<Step>("landing");
  const [formData, setFormData] = useState<FormData | null>(null);
  const [sessionToken, setSessionToken] = useState<string>("");
  const [prize, setPrize] = useState<PrizeData | null>(null);

  const handleFormSubmit = (data: FormData) => {
    setFormData(data);
    setStep("otp");
  };

  const handleOtpVerified = (token: string) => {
    setSessionToken(token);
    setStep("prize");
  };

  const handleRegistered = (prizeData: PrizeData) => {
    setPrize(prizeData);
  };

  return (
    <>
      <Head>
        <title>NIRVIZ Resort — Spin & Win</title>
        <meta name="description" content="Register and win exciting prizes at NIRVIZ Resort!" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
      </Head>

      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-10">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-brand-dark">NIRVIZ Resort</h1>
          <p className="text-gray-500 mt-1 text-sm">Fast Food &amp; Cafe</p>
        </div>

        {/* Step card */}
        <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-6">
          {step === "landing" && (
            <ReviewPrompt onRegister={() => setStep("form")} />
          )}
          {step === "form" && (
            <CustomerForm onSubmit={handleFormSubmit} />
          )}
          {step === "otp" && formData && (
            <OtpInput
              phone={formData.phone}
              email={formData.email}
              onVerified={handleOtpVerified}
              onBack={() => setStep("form")}
            />
          )}
          {step === "prize" && formData && (
            <PrizeReveal
              formData={formData}
              sessionToken={sessionToken}
              prize={prize}
              onRegistered={handleRegistered}
            />
          )}
        </div>
      </main>
    </>
  );
}
