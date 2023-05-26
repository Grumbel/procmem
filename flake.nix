{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
    flake-utils.url = "github:numtide/flake-utils";

    bytefmt.url = "github:grumbel/python-bytefmt";
    bytefmt.inputs.nixpkgs.follows = "nixpkgs";
    bytefmt.inputs.flake-utils.follows = "flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, bytefmt }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python310Packages;
      in rec {
        packages = rec {
          default = procmem;

          procmem = pythonPackages.buildPythonPackage rec {
            pname = "procmem";
            version = "0.1.0";

            src = ./.;

            checkPhase = ''
              runHook preCheck
              flake8 procmem tests
              pyright procmem tests
              mypy procmem tests
              # pylint procmem tests
              python3 -m unittest discover -v -s tests/
              runHook postCheck
            '';

            nativeCheckInputs = (with pkgs; [
              pyright
            ]) ++ (with pythonPackages; [
              flake8
              mypy
              pylint
              types-setuptools
            ]);

            propagatedBuildInputs = [
              pythonPackages.setuptools
              pythonPackages.psutil
              pythonPackages.pillow
              (bytefmt.lib.bytefmtWithPythonPackages pythonPackages)
            ];
          };
        };
      }
    );
}
