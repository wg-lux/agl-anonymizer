{
  description = "Python application packaged using poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, flake-utils, cachix, poetry2nix }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
        config.cudaSupport = true;
      };
      nvidiaCache = cachix.lib.mkCachixCache {
          inherit (pkgs) lib;
          name = "nvidia";
          publicKey = "nvidia.cachix.org-1:dSyZxI8geDCJrwgvBfPH3zHMC+PO6y/BT7O6zLBOv0w=";
          secretKey = null;  # not needed for pulling from the cache
      };

      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
      myPythonApp = mkPoetryApplication { projectDir = ../agl-censor; };
    in {
      apps = {
        ${system} = {
          default = {
            type = "app";
            program = "${myPythonApp}/bin/agl-censor";  # Make sure this is the correct executable path
          };
        };
      };

      defaultApp = self.apps.${system}.default;

      devShell.${system} = pkgs.mkShell {
        buildInputs = with pkgs; [ 
          poetry
          stdenv.cc.cc.lib
          opencv
          autoAddDriverRunpath
          cudaPackages.cudatoolkit
          libGLU libGL
          glibc
          zlib
          glib
          xorg.libXi xorg.libXmu freeglut
          xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib 
          ncurses5 stdenv.cc binutils
          python311
          python311Packages.dulwich
          python311Packages.pandas
          python311Packages.pytesseract
          python311Packages.venvShellHook
          python311Packages.numpy
          python311Packages.imutils

          pam
        ];
        venvDir = ".venv";
        postShellHook = ''
          export CUDA_PATH=${pkgs.cudatoolkit}
          export LD_LIBRARY_PATH="${pkgs.linuxPackages.nvidia_x11}/lib:${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glib}/lib:${pkgs.glibc}/lib:/nix/store/3xsbahrqqc4fc3gknmjj9j9687n4hiz0-glib-2.80.0/lib/:$LD_LIBRARY_PATH"
          export EXTRA_LDFLAGS="-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib"
          export EXTRA_CCFLAGS="-I/usr/include"

          python -m pip install --upgrade pip
          poetry update

        '';
      };

      nixConfig = {
        binary-caches = [nvidiaCache.binaryCachePublicUrl];
        binary-cache-public-keys = [nvidiaCache.publicKey];
      };
    };
}
