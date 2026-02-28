#!/bin/bash
echo "Arrêt des containers Transport Quote..."

# Arrêt mode local
docker-compose -f docker-compose.yml -f docker-compose.local.yml down 2>/dev/null

# Arrêt mode prod (au cas où)
docker-compose -f docker-compose.yml down 2>/dev/null

# Déconnecter et supprimer tout container encore attaché aux réseaux du projet
for network in transport_quote_app-network transport_quote_dmz-network; do
  containers=$(docker network inspect "$network" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)
  if [ -n "$containers" ]; then
    echo "Containers encore connectés à $network : $containers"
    for container in $containers; do
      echo "  Déconnexion de $container..."
      docker network disconnect -f "$network" "$container" 2>/dev/null
    done
  fi
done

echo "Containers arrêtés."
