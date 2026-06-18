import React from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';

const Footer = () => {
  const { user } = useUser();

  return (
    <footer className="bg-background py-12 border-t border-border mt-auto w-full">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="col-span-1 md:col-span-2">
          <div className="flex items-center gap-2 text-primary font-heading font-bold text-xl mb-4">
            <iconify-icon icon="lucide:activity"></iconify-icon>
            <span>MediAI</span>
          </div>
          <p className="text-sm text-muted-foreground max-w-sm mb-6">
            Empowering patients and professionals with AI-driven medical insights, drug interaction checks, and
            comprehensive disease data.
          </p>
          <p className="text-xs text-muted-foreground">
            Disclaimer: MediAI is for informational purposes only and does not replace professional medical advice.
          </p>
        </div>
        <div>
          <h4 className="font-semibold text-foreground mb-4">Product</h4>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li><Link to={user ? "/app/chat" : "/chat"} className="hover:text-primary transition-colors">AI Chatbot</Link></li>
            <li><Link to={user ? "/app/medicines" : "/medicines"} className="hover:text-primary transition-colors">Medicine Lookup</Link></li>
            <li><Link to={user ? "/app/interactions" : "/login"} className="hover:text-primary transition-colors">Interaction Checker</Link></li>
            <li><Link to="/pricing" className="hover:text-primary transition-colors">Pricing</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-foreground mb-4">Company</h4>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li><a href="#careers" className="hover:text-primary transition-colors">Careers</a></li>
            <li><a href="#privacy" className="hover:text-primary transition-colors">Privacy Policy</a></li>
            <li><a href="#terms" className="hover:text-primary transition-colors">Terms of Service</a></li>
          </ul>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
