import React from 'react';
import LandingFlowGraph from './components/LandingFlowGraph';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white">
      {/* Header */}
      <header className="text-center py-16 px-6">
        <h1 className="text-5xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'Aeonik, sans-serif' }}>
          Advanced Explainable AI Toolkit
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          Understand how AI models make decisions through multiple explanation methods. 
          Visualize token importance, attention flows, and causal relationships in real-time.
        </p>
      </header>

      {/* Main Flow Graph */}
      <main className="max-w-6xl mx-auto px-6 pb-16">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-2" style={{ fontFamily: 'Aeonik, sans-serif' }}>
              How It Works
            </h2>
            <p className="text-gray-600">
              Input text flows through our explanation pipeline to generate comprehensive insights
            </p>
          </div>
          
          <div className="flex justify-center">
            <LandingFlowGraph width={700} height={300} />
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <div className="w-6 h-6 bg-purple-600 rounded-full"></div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2" style={{ fontFamily: 'Aeonik, sans-serif' }}>
              Token Analysis
            </h3>
            <p className="text-gray-600 text-sm">
              LIME and SHAP methods identify which tokens contribute most to model predictions
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <div className="w-6 h-6 bg-purple-600 rounded-full"></div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2" style={{ fontFamily: 'Aeonik, sans-serif' }}>
              Attention Flow
            </h3>
            <p className="text-gray-600 text-sm">
              Visualize how neural networks process information through attention mechanisms
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <div className="w-6 h-6 bg-purple-600 rounded-full"></div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2" style={{ fontFamily: 'Aeonik, sans-serif' }}>
              Causal Analysis
            </h3>
            <p className="text-gray-600 text-sm">
              Understand cause-effect relationships in model decision-making processes
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <button className="bg-purple-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-purple-700 transition-colors duration-200 shadow-lg hover:shadow-xl" style={{ fontFamily: 'Aeonik, sans-serif' }}>
            Try the Toolkit
          </button>
          <p className="text-gray-500 mt-3 text-sm">
            No installation required • Works with any AI model
          </p>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
