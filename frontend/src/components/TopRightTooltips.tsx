"use client";

import React from "react";
import { AnimatedTooltip } from "./ui/animated-tooltip";

interface TopRightTooltipsProps {
  isProcessing?: boolean;
  hasInputText?: boolean;
  hasExplanations?: boolean;
}

const TopRightTooltips: React.FC<TopRightTooltipsProps> = ({ 
  isProcessing = false, 
  hasInputText = false, 
  hasExplanations = false 
}) => {
  // Team members with specified names
  const people = [
    {
      id: 1,
      name: "Pranav Reddy Gaddam",
      designation: "AI Research Lead",
      image: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face",
    },
    {
      id: 2,
      name: "Pulkit Srivastava",
      designation: "Machine Learning Expert",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
    },
    {
      id: 3,
      name: "Shweta Shinde",
      designation: "Data Science Director",
      image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
    },
    {
      id: 4,
      name: "Gayatri Patil",
      designation: "XAI Methods Researcher",
      image: "https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=150&h=150&fit=crop&crop=face",
    },
  ];

  // Hide tooltips when there's any interaction (input text, processing, or explanations)
  if (isProcessing || hasInputText || hasExplanations) {
    return null;
  }

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
      <div className="flex items-center justify-center">
        <AnimatedTooltip items={people} />
      </div>
    </div>
  );
};

export default TopRightTooltips;
