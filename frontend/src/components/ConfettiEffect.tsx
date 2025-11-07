import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

interface ConfettiEffectProps {
  trigger: boolean;
  onComplete?: () => void;
}

const ConfettiEffect: React.FC<ConfettiEffectProps> = ({ trigger, onComplete }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!trigger || !containerRef.current) return;

    const container = containerRef.current;
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    const confettiPieces: HTMLElement[] = [];

    // Create confetti pieces
    for (let i = 0; i < 50; i++) {
      const piece = document.createElement('div');
      piece.style.position = 'fixed';
      piece.style.width = '8px';
      piece.style.height = '8px';
      piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      piece.style.borderRadius = '50%';
      piece.style.pointerEvents = 'none';
      piece.style.zIndex = '9999';
      
      // Random starting position
      const startX = Math.random() * window.innerWidth;
      const startY = -10;
      
      piece.style.left = `${startX}px`;
      piece.style.top = `${startY}px`;
      
      container.appendChild(piece);
      confettiPieces.push(piece);
    }

    // Animate confetti
    confettiPieces.forEach((piece, index) => {
      const randomX = (Math.random() - 0.5) * 400;
      const randomY = Math.random() * 600 + 300;
      const randomRotation = Math.random() * 720;
      const randomDelay = Math.random() * 0.5;

      gsap.set(piece, { 
        scale: 0,
        rotation: 0,
        x: 0,
        y: 0
      });

      gsap.to(piece, {
        scale: Math.random() * 1.5 + 0.5,
        rotation: randomRotation,
        x: randomX,
        y: randomY,
        duration: 2 + Math.random() * 2,
        delay: randomDelay,
        ease: "power2.out",
        onComplete: () => {
          gsap.to(piece, {
            scale: 0,
            opacity: 0,
            duration: 0.5,
            ease: "power2.in",
            onComplete: () => {
              piece.remove();
              if (confettiPieces.indexOf(piece) === confettiPieces.length - 1) {
                onComplete?.();
              }
            }
          });
        }
      });
    });

    // Cleanup function
    return () => {
      confettiPieces.forEach(piece => {
        if (piece.parentNode) {
          piece.remove();
        }
      });
    };
  }, [trigger, onComplete]);

  return <div ref={containerRef} style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 9999 }} />;
};

export default ConfettiEffect;
