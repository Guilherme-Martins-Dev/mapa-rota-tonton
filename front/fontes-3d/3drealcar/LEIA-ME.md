# Onde extrair o 3DRealCar

Coloque aqui, em UMA subpasta por carro, o que baixar do dataset 3DRealCar
(https://xiaobiaodu.github.io/3drealcar/download.html, OneDrive ou Google Drive):

    front/fontes-3d/3drealcar/
      carro-01/
        texture_output.obj
        texture_output.mtl
        (texturas .jpg/.png que o .mtl cita)

Basta UM carro para começar. Escolha um sedã ou hatch de cor lisa, de preferência sem muito reflexo no scan.

- Esta pasta está no .gitignore: o dataset é grande e NÃO deve ir para o repositório público.
- O que entra no site é só o .glb leve gerado a partir daqui (`npm run modelos`), em `front/public/models/`.
- Licença do dataset: Apache-2.0 (uso comercial liberado), exige manter o aviso e citar:
  Du et al., "3DRealCar: An In-the-wild RGB-D Car Dataset with 360-degree Views", ICCV 2025.
