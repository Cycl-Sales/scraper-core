import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";

interface LoadingAnimationProps {
  size?: "sm" | "md" | "lg";
  message?: string;
}

export default function LoadingAnimation({ size = "md", message = "Loading..." }: LoadingAnimationProps) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-12 h-12", 
    lg: "w-16 h-16"
  };

  const containerSizes = {
    sm: "min-h-[100px]",
    md: "min-h-[200px]",
    lg: "min-h-[300px]"
  };

  return (
    <div className={`flex flex-col items-center justify-center ${containerSizes[size]} space-y-4`}>
      {/* Animated Brand Character */}
      <div className="relative">
        {/* Main character - animated chart icon */}
        <motion.div
          className={`${sizeClasses[size]} bg-blue-600 rounded-lg flex items-center justify-center relative overflow-hidden`}
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <BarChart3 className="w-6 h-6 text-white" />
          
          {/* Animated glow effect */}
          <motion.div
            className="absolute inset-0 bg-blue-400 rounded-lg opacity-30"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </motion.div>

        {/* Floating data points around the character */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full"
            style={{
              top: `${20 + Math.sin(i * Math.PI / 3) * 30}px`,
              left: `${20 + Math.cos(i * Math.PI / 3) * 30}px`,
            }}
            animate={{
              y: [-5, 5, -5],
              opacity: [0.4, 1, 0.4],
              scale: [0.8, 1.2, 0.8],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut"
            }}
          />
        ))}
      </div>

      {/* Animated loading text */}
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
        
        {/* Animated dots */}
        <div className="flex justify-center space-x-1 mt-2">
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 bg-blue-400 rounded-full"
              animate={{
                y: [-3, 0, -3],
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </motion.div>

      {/* Progress bar animation */}
      <div className="w-32 h-1 bg-slate-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
          animate={{
            x: [-128, 128],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          style={{ width: "50%" }}
        />
      </div>
    </div>
  );
}

// Skeleton loader component for cards
export function LoadingSkeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="bg-slate-800 rounded-lg p-6 space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-slate-700 rounded-lg"></div>
          <div className="space-y-2 flex-1">
            <div className="h-4 bg-slate-700 rounded w-3/4"></div>
            <div className="h-3 bg-slate-700 rounded w-1/2"></div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-20 bg-slate-700 rounded"></div>
          <div className="grid grid-cols-3 gap-2">
            <div className="h-4 bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Table skeleton loader
export function TableLoadingSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="animate-pulse">
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        {/* Table header */}
        <div className="bg-slate-800 px-6 py-4 border-b border-slate-700">
          <div className="grid grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-slate-700 rounded"></div>
            ))}
          </div>
        </div>
        
        {/* Table rows */}
        <div className="divide-y divide-slate-800">
          {[...Array(rows)].map((_, i) => (
            <div key={i} className="px-6 py-4">
              <div className="grid grid-cols-5 gap-4 items-center">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-slate-700 rounded-full"></div>
                  <div className="h-4 bg-slate-700 rounded w-24"></div>
                </div>
                <div className="h-4 bg-slate-700 rounded w-20"></div>
                <div className="h-4 bg-slate-700 rounded w-16"></div>
                <div className="h-4 bg-slate-700 rounded w-12"></div>
                <div className="w-16 h-6 bg-slate-700 rounded-full"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}