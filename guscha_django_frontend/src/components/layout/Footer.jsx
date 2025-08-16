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
      <div className="footer-content">
        <ul className="footer-list">
          <li className="footer-list-title">CATEGORIES</li>
          {categories.map(cat => (
            <li key={cat} className="footer-list-item">{cat}</li>
          ))}
        </ul>
        <ul className="footer-list">
          <li className="footer-list-title">INFORMATION</li>
          {info.map(item => (
            <li key={item} className="footer-list-item-regular">{item}</li>
          ))}
        </ul>
        <ul className="footer-list-social">
          <li className="footer-list-title">FOLLOW US</li>
          {socials.map(s => (
            <li key={s.name} className="footer-list-item"><a href={s.url} className="footer-social-link">{s.name}</a></li>
          ))}
        </ul>
      </div>
    </footer>
  );
}