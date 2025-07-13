import React from 'react';
import Input from '../../ui/Input';
import Button from '../../ui/Button';

const AuthForm = ({ onSubmit, loading, error, fields, submitText = 'Войти' }) => {
  const [form, setForm] = React.useState(() => {
    const initial = {};
    fields.forEach(f => { initial[f.name] = f.value || ''; });
    return initial;
  });

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      {fields.map(f => (
        <Input
          key={f.name}
          label={f.label}
          name={f.name}
          type={f.type || 'text'}
          value={form[f.name]}
          onChange={handleChange}
          placeholder={f.placeholder}
          error={f.error}
        />
      ))}
      {error && <div className="auth-form-error">{error}</div>}
      <Button type="submit" disabled={loading} className="auth-form-submit">
        {loading ? 'Загрузка...' : submitText}
      </Button>
    </form>
  );
};

export default AuthForm; 