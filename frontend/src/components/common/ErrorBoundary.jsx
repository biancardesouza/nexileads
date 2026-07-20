import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { comErro: false };
  }

  static getDerivedStateFromError() {
    return { comErro: true };
  }

  componentDidCatch(error, info) {
    console.error("Erro inesperado na interface:", error, info);
  }

  render() {
    if (this.state.comErro) {
      return (
        <div className="container">
          <header>
            <h1>Algo deu errado</h1>
            <p>Ocorreu um erro inesperado nessa tela. Tente recarregar a página.</p>
          </header>
          <button className="btn-primary" onClick={() => window.location.reload()}>
            Recarregar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
