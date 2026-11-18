import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

interface InversionCircleScrollAnimationProps {
  onExplore?: () => void;
}

const headline = 'Investing should make sense before it makes money.';
const description = 'Hindsight is an educational robo-advisor simulation that helps you understand risk, explore rule-based portfolio recommendations and practise investing with virtual INR.';

function IntroductionCopy({ onExplore }: { onExplore?: () => void }) {
  return <div className="mx-auto grid w-full max-w-7xl gap-10 px-6 lg:grid-cols-[1.15fr_.85fr] lg:items-center lg:gap-16 lg:px-16">
    <div><p className="text-xs font-semibold uppercase tracking-[.2em] text-[#4C9B79]">THE FIRST PRINCIPLE</p><h2 className="mt-5 max-w-3xl font-display text-4xl font-medium leading-[1.02] tracking-tight sm:text-5xl lg:text-7xl">{headline}</h2></div>
    <div className="max-w-xl border-l border-[#C9A66B] pl-6"><p className="text-lg leading-8 text-[#A5A5A0]">{description}</p><button onClick={onExplore} className="group mt-7 inline-flex items-center gap-2 text-sm font-semibold text-[#E8E5D5] transition-all hover:gap-3">Create an account <ArrowRight size={16}/></button></div>
  </div>;
}

export default function InversionCircleScrollAnimation({ onExplore }: InversionCircleScrollAnimationProps) {
  const reduceMotion = useReducedMotion();
  return <section id="introduction" className="relative bg-[#080808] pb-24 pt-20 sm:pb-32 sm:pt-28" aria-label="Hindsight introduction">
    <motion.div initial={reduceMotion ? false : { y: 30, opacity: 0 }} whileInView={{ y: 0, opacity: 1 }} viewport={{ once: true, amount: 0.2 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }} className="text-[#E8E5D5]">
      <IntroductionCopy onExplore={onExplore}/>
    </motion.div>
  </section>;
}
