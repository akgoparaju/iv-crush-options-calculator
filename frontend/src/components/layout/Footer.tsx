import React from 'react'
import { Heart, Shield, AlertTriangle } from 'lucide-react'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        {/* Educational Disclaimer - Prominent */}
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-warning-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-warning-800 mb-1">
                Educational Use Only - Not Financial Advice
              </p>
              <p className="text-warning-700">
                This calculator is designed for educational purposes to help understand options trading concepts. 
                All analysis and recommendations are for learning only. Always consult with a qualified financial 
                advisor before making investment decisions. Trading options involves significant risk and may not 
                be suitable for all investors.
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          {/* Left side - Copyright and version */}
          <div className="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-6">
            <p className="text-sm text-slate-600">
              © 2025 Advanced Options Trading Calculator v2.0.0
            </p>
            <div className="flex items-center space-x-4 text-sm text-slate-500">
              <span className="flex items-center">
                <Shield className="h-4 w-4 mr-1" />
                Educational License
              </span>
              <span>For Learning Purposes Only</span>
            </div>
          </div>

          {/* Right side - Made with */}
          <div className="flex items-center space-x-2 text-sm text-slate-600">
            <span>Built with</span>
            <Heart className="h-4 w-4 text-danger-500" />
            <span>for education</span>
          </div>
        </div>
        
        {/* Additional links */}
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm">
            <a 
              href="#" 
              className="text-slate-500 hover:text-slate-700 transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Privacy Policy
            </a>
            <a 
              href="#" 
              className="text-slate-500 hover:text-slate-700 transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Terms of Use
            </a>
            <a 
              href="#" 
              className="text-slate-500 hover:text-slate-700 transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Risk Disclosures
            </a>
            <a 
              href="#" 
              className="text-slate-500 hover:text-slate-700 transition-colors"
              onClick={(e) => e.preventDefault()}
            >
              Educational Resources
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}