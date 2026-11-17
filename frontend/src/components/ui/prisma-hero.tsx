import { motion, useInView, useReducedMotion } from 'framer-motion';
import { ArrowDown, ArrowRight } from 'lucide-react';
import { useRef, useState, type CSSProperties } from 'react';

interface WordsPullUpProps {
  text: string;
  className?: string;
  showAsterisk?: boolean;
  style?: CSSProperties;
}

export const WordsPullUp = ({ text, className = '', showAsterisk = false, style }: WordsPullUpProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true });
  const reduceMotion = useReducedMotion();
  const words = text.split(' ');

  return <div ref={ref} className={`inline-flex flex-wrap ${className}`} style={style}>
    {words.map((word, i) => {
      const isLast = i === words.length - 1;
      return <motion.span key={i} initial={reduceMotion ? false : { y: 20, opacity: 0 }} animate={reduceMotion || isInView ? { y: 0, opacity: 1 } : {}} transition={{ duration: 0.6, delay: reduceMotion ? 0 : i * 0.08, ease: [0.16, 1, 0.3, 1] }} className="relative inline-block" style={{ marginRight: isLast ? 0 : '0.25em' }}>
        {word}{showAsterisk && isLast && <span className="absolute -right-[0.3em] top-[0.65em] text-[0.31em]">*</span>}
      </motion.span>;
    })}
  </div>;
};

interface Segment { text: string; className?: string }
export const WordsPullUpMultiStyle = ({ segments, className = '', style }: { segments: Segment[]; className?: string; style?: CSSProperties }) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true });
  const reduceMotion = useReducedMotion();
  const words: { word: string; className?: string }[] = [];
  segments.forEach((segment) => segment.text.split(' ').forEach((word) => word && words.push({ word, className: segment.className })));
  return <div ref={ref} className={`inline-flex flex-wrap justify-center ${className}`} style={style}>{words.map((word, i) => <motion.span key={i} initial={reduceMotion ? false : { y: 20, opacity: 0 }} animate={reduceMotion || isInView ? { y: 0, opacity: 1 } : {}} transition={{ duration: 0.6, delay: reduceMotion ? 0 : i * 0.08, ease: [0.16, 1, 0.3, 1] }} className={`inline-block ${word.className ?? ''}`} style={{ marginRight: '0.25em' }}>{word.word}</motion.span>)}</div>;
};

const navItems = [
  { label: 'How it works', href: '#how-it-works' },
  { label: 'Features', href: '#features' },
  { label: 'Our approach', href: '#approach' },
  { label: 'Learn', href: '#learn' },
  { label: 'Contact', href: '#contact' },
];

interface PrismaHeroProps { onTryDemo: () => void; loading?: boolean; activeSection?: string }

export const PrismaHero = ({ onTryDemo, loading = false, activeSection = 'hero' }: PrismaHeroProps) => {
  const [videoFailed, setVideoFailed] = useState(false);
  const reduceMotion = useReducedMotion();
  const contentMotion = { initial: reduceMotion ? false : { y: 20, opacity: 0 }, animate: { y: 0, opacity: 1 }, transition: { duration: 0.8, delay: reduceMotion ? 0 : 0.5, ease: [0.16, 1, 0.3, 1] as const } };

  return <section className="relative isolate h-screen min-h-[620px] w-full bg-[#080808] px-0 sm:px-3 sm:pt-3">
    <div className="pointer-events-none absolute -inset-5 -z-10 rounded-[2.75rem] bg-[radial-gradient(ellipse_at_center,rgba(24,24,24,.75)_45%,rgba(8,8,8,0)_78%)] opacity-90 blur-2xl" />
    <div className="relative h-full w-full overflow-hidden rounded-none bg-[#111111] sm:rounded-2xl md:rounded-[2rem]">
      {!videoFailed && <video autoPlay loop muted playsInline onError={() => setVideoFailed(true)} className="absolute inset-0 h-full w-full object-cover" src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260405_170732_8a9ccda6-5cff-4628-b164-059c500a2b41.mp4" />}
      <div className="noise-overlay pointer-events-none absolute inset-0 opacity-[0.7] mix-blend-overlay" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-black/35 via-black/10 to-black/85" />
      <nav className="absolute left-4 right-4 top-5 z-20 sm:left-1/2 sm:right-auto sm:top-7 sm:w-max sm:-translate-x-1/2">
        <div className="scrollbar-hidden flex max-w-full items-center justify-center gap-2 overflow-x-auto rounded-full border border-white/10 bg-black/80 px-3 py-2.5 shadow-xl shadow-black/20 backdrop-blur-sm sm:gap-6 sm:px-6 md:gap-10 md:px-8 lg:gap-12">
          {navItems.map((item) => <a key={item.label} href={item.href} className={`whitespace-nowrap text-[10px] transition-colors sm:text-xs md:text-sm ${activeSection === item.href.slice(1) ? 'text-[#E8E5D5]' : 'text-[#E8E5D5]/65 hover:text-[#E8E5D5]'}`}>{item.label}</a>)}
        </div>
      </nav>
      <div className="absolute bottom-[10vh] left-0 right-0 px-5 sm:bottom-[13vh] sm:px-8 md:px-10 lg:bottom-[15vh]">
        <div className="mx-auto grid max-w-[1600px] grid-cols-1 items-end gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,.65fr)] lg:gap-12">
          <div className="min-w-0"><div className="mb-5 flex items-center gap-3 text-[10px] font-semibold uppercase tracking-[.2em] text-[#E8E5D5]/70 sm:text-xs"><span className="h-px w-8 bg-[#E8E5D5]/50"/> A clearer way to learn wealth</div><h1 className="whitespace-nowrap font-medium text-[clamp(4.5rem,11.5vw,10.5rem)] leading-[0.84] tracking-[-0.075em] text-[#E8E5D5]"><WordsPullUp text="Hindsight" showAsterisk /></h1></div>
          <div className="flex max-w-[390px] flex-col gap-5 pb-0 lg:pb-1">
            <motion.p {...contentMotion} className="text-xs text-[#A5A5A0] sm:text-sm md:text-base" style={{ lineHeight: 1.2 }}>A smarter way to understand investing. Discover your risk profile, explore personalised portfolio recommendations and practise building wealth with virtual INR.</motion.p>
            <motion.button {...contentMotion} transition={{ duration: 0.8, delay: reduceMotion ? 0 : 0.7, ease: [0.16, 1, 0.3, 1] }} onClick={onTryDemo} disabled={loading} className="group inline-flex items-center gap-2 self-start rounded-full bg-[#E8E5D5] py-1 pl-5 pr-1 text-sm font-medium text-black transition-all hover:gap-3 disabled:cursor-wait disabled:opacity-70 sm:text-base">{loading ? 'Opening demo…' : 'Try the demo'}<span className="flex h-9 w-9 items-center justify-center rounded-full bg-black transition-transform group-hover:scale-110 sm:h-10 sm:w-10"><ArrowRight className="h-4 w-4 text-[#E8E5D5]" /></span></motion.button>
          </div>
        </div>
      </div>
      <a href="#introduction" className="absolute bottom-7 left-1/2 z-10 hidden -translate-x-1/2 flex-col items-center gap-2 text-[10px] uppercase tracking-[.2em] text-[#A5A5A0] transition hover:text-[#E8E5D5] sm:flex"><span>Scroll to explore</span><motion.span animate={reduceMotion ? undefined : { y: [0, 5, 0] }} transition={reduceMotion ? undefined : { duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}><ArrowDown size={14}/></motion.span></a>
    </div>
  </section>;
};

export default PrismaHero;
