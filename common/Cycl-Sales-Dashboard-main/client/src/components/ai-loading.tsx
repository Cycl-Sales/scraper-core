import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";

interface AILoadingProps {
  message?: string;
  size?: "sm" | "md" | "lg";
}

export default function AILoading({ message = "AI is thinking...", size = "md" }: AILoadingProps) {
  const sizeClasses = {
    sm: "w-10 h-10",
    md: "w-16 h-16",
    lg: "w-20 h-20"
  };

  const containerSizes = {
    sm: "min-h-[80px]",
    md: "min-h-[120px]",
    lg: "min-h-[160px]"
  };

  return (
    <div className={`flex flex-col items-center justify-center ${containerSizes[size]} space-y-4`}>
      {/* AI Brain Character */}
      <div className="relative">
        <motion.div
          className={`${sizeClasses[size]} bg-gradient-to-br from-purple-600 via-blue-600 to-cyan-500 rounded-full flex items-center justify-center relative overflow-hidden`}
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 360],
          }}
          transition={{
            scale: {
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            },
            rotate: {
              duration: 8,
              repeat: Infinity,
              ease: "linear"
            }
          }}
        >
          <Brain className="w-8 h-8 text-white" />
          
          {/* Neural network effect */}
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{
              background: "radial-gradient(circle, rgba(147, 51, 234, 0.3) 0%, transparent 70%)"
            }}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.3, 0.8, 0.3],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </motion.div>

        {/* Floating sparkles around the brain */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute"
            style={{
              top: `${50 + Math.sin(i * Math.PI / 4) * 40}%`,
              left: `${50 + Math.cos(i * Math.PI / 4) * 40}%`,
            }}
            animate={{
              y: [-10, 10, -10],
              x: [-5, 5, -5],
              opacity: [0.2, 1, 0.2],
              scale: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 2 + i * 0.3,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut"
            }}
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
          </motion.div>
        ))}

        {/* Energy pulse rings */}
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute inset-0 border-2 border-purple-400 rounded-full opacity-30"
            animate={{
              scale: [1, 2, 2],
              opacity: [0.6, 0.2, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.6,
              ease: "easeOut"
            }}
          />
        ))}
      </div>

      {/* AI thinking text with typing effect */}
      <motion.div
        className="text-slate-300 text-center"
        animate={{
          opacity: [0.6, 1, 0.6],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <p className="text-sm font-medium">{message}</p>
        
        {/* Animated typing dots */}
        <div className="flex justify-center space-x-1 mt-2">
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-purple-400 rounded-full"
              animate={{
                y: [-4, 0, -4],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// Small inline loading spinner for buttons
export function ButtonSpinner({ size = "sm" }: { size?: "sm" | "md" }) {
  const spinnerSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";
  
  return (
    <motion.div
      className={`${spinnerSize} border-2 border-white/30 border-t-white rounded-full`}
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: "linear"
      }}
    />
  );
}

// Floating data orbs animation
export function DataOrbs() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(6)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-4 h-4 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full opacity-60"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [-20, -40, -20],
            x: [-10, 10, -10],
            opacity: [0.6, 0.2, 0.6],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: i * 0.5,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
}