# Créditos dos modelos 3D

## Carro (hero e viagem)

- **Modelo:** "Toyota Corola", de danieljorge435. https://sketchfab.com/3d-models/toyota-corola-aab1b90a73f7416890c31a8927cc5038
- **Licença:** Creative Commons Attribution (CC BY 4.0), confirmada na API do Sketchfab e no campo `license` do metadado do MeshFleet.
- **Como chegou aqui:** listado no dataset MeshFleet (Boborzi et al., https://github.com/FeMa42/MeshFleet, https://huggingface.co/datasets/DamianBoborzi/MeshFleet), baixado de `meshes/aab1b90a73f7416890c31a8927cc5038.glb`.
- **Alterações:** escala para 4,4 unidades de comprimento, giro de 90° para a frente apontar para +X, centralização e apoio em y = 0 (`front/scripts/converter-carro.mjs`). Malha e texturas não foram editadas. Resultado: `front/public/models/carro-corolla.glb`.
- A licença Apache-2.0 do MeshFleet cobre o código e os metadados dele, não os modelos: cada modelo mantém a licença do autor. Por isso a licença foi conferida modelo a modelo.

## Candidato descartado

O "1968 Volkswagen Beetle (LP)" (Sketchfab, KrStolorz) aparece como CC-BY no CSV do MeshFleet, mas a API do Sketchfab informa a licença "Free Standard". Como as duas fontes divergem, o modelo não foi usado.

## Demais modelos

`carro.glb` (reserva), prédios, torres, comércio, casa e médio são gerados por código em `front/scripts/gerar-modelos.mjs`, sem material de terceiros.

## 3DRealCar (não usado)

O repositório 3DRealCar_Toolkit só contém código de pré-processamento; as texturas ficam em um dataset de scans em pastas de OneDrive/Google Drive. Foi substituído pelo MeshFleet por decisão do projeto.
