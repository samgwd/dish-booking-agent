.PHONY: dev infra backend frontend stop logs clean help

# Default target
help:
	@echo "DiSH Booking Agent - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  dev       Start all services (infra + backend + frontend)"
	@echo "  infra     Start infrastructure only (databases + Keycloak)"
	@echo "  backend   Start the FastAPI backend server"
	@echo "  frontend  Start the Next.js frontend server"
	@echo "  stop      Stop all running services"
	@echo "  logs      Tail Docker container logs"
	@echo "  clean     Stop services and remove Docker volumes"
	@echo "  help      Show this help message"

# Start everything
dev: infra
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 5
	@$(MAKE) -j2 backend frontend

# Start infrastructure (databases + Keycloak)
infra:
	@echo "🐳 Starting Docker services..."
	docker compose up -d
	@echo "✅ Infrastructure started"
	@echo "   Keycloak Admin: http://localhost:8080"

# Start backend API
backend:
	@echo "🚀 Starting backend API..."
	cd backend && uv run uvicorn src.api:app --reload --port 8000

# Start frontend
frontend:
	@echo "🎨 Starting frontend..."
	cd frontend && bun dev

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	-docker compose down
	-pkill -f "uvicorn src.api:app" 2>/dev/null || true
	-pkill -f "next dev" 2>/dev/null || true
	@echo "✅ All services stopped"

# View Docker logs
logs:
	docker compose logs -f

# Clean up everything including volumes
clean: stop
	@echo "🧹 Removing Docker volumes..."
	docker compose down -v
	@echo "✅ Clean complete"
