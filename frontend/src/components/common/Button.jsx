const Button = ({ onClick, children, variant = 'primary', disabled = false, className = '' }) => {
  const baseClasses = 'px-6 py-3 rounded-lg font-semibold transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    success: 'bg-green-600 text-white hover:bg-green-700',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

export default Button;
