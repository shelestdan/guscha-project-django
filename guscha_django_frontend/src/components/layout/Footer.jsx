import React from 'react';
import '../../styles/Footer.css';

const categories = [
  'APPAREL', 'GOODS', 'COLLECTIBLES', 'BOOKS', 'AJAJA',
];
const info = [
  'SHIPPING & RETURNS', 'TERMS OF USE', 'PRIVACY POLICY', 'DO NOT SELL OR SHARE MY PERSONAL INFORMATION',
];
const socials = [
  { name: 'TWITTER', url: '#' },
  { name: 'TIKTOK', url: '#' },
  { name: 'INSTAGRAM', url: '#' },
  { name: 'YOUTUBE', url: '#' },
];

export default function Footer() {
  return (
    <footer id="contacts" className="footer-main">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <ul className="footer-list">
              {categories.map(cat => (
                <li key={cat} className="footer-list-item">{cat}</li>
              ))}
            </ul>
          </div>
          <div className="footer-section-wide">
            <ul className="footer-list">
              {info.map(item => (
                <li key={item} className="footer-list-item-regular">{item}</li>
              ))}
            </ul>
          </div>
          <div className="footer-section-social">
            <ul className="footer-list-social">
              {socials.map(s => (
                <li key={s.name}><a href={s.url} className="footer-social-link">{s.name}</a></li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
} 