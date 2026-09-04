/** Build-time only. Colors/shadows are the real Mintek design tokens - see
 * dashboard/README-BUILD.md and HANDOVER entry 36/37 for provenance. */
module.exports = {
  content: ["../templates/**/*.jinja"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#00131D",
        surface: "#071C27",
        "surface-container": "#0B222E",
        "surface-container-high": "#102C3B",
        "surface-container-highest": "#194D5C",
        "surface-container-lowest": "#000D14",
        outline: "#1E3E4B",
        "outline-dim": "#132D37",
        primary: "#D22D20",
        "primary-light": "#FF5747",
        "on-surface": "#E3EAEB",
        "on-surface-variant": "#8CA6AE",
        "secondary-teal": "#194D5C",
        "teal-accent": "#2EA5BC",
        success: "#1EA868",
        "success-container": "#062B1A",
        warning: "#FFB539",
        "warning-container": "#3D2A00",
        danger: "#D22D20",
        "danger-container": "#3A0704",
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        "elevation-1": "0 4px 20px -2px rgba(0,19,29,0.8), 0 0 0 1px rgba(30,62,75,0.55)",
        "elevation-2": "0 8px 32px -4px rgba(0,13,20,0.9), 0 0 0 1px rgba(30,62,75,0.7)",
        "elevation-accent": "0 12px 40px -8px rgba(210,45,32,0.25), 0 0 0 1px rgba(210,45,32,0.4)",
        "glow-success": "0 0 20px -3px rgba(30,168,104,0.35)",
        "glow-danger": "0 0 24px -3px rgba(210,45,32,0.4)",
        "glow-warning": "0 0 20px -3px rgba(255,181,57,0.35)",
      },
      animation: {
        "fade-up": "fadeUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards",
        "pulse-subtle": "pulseSubtle 3s cubic-bezier(0.4,0,0.6,1) infinite",
      },
      keyframes: {
        fadeUp: { "0%": { opacity: 0, transform: "translateY(12px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        pulseSubtle: { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.4 } },
      },
    },
  },
  plugins: [],
};
