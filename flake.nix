{
  description = "Python/SVG/Video environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };

        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pillow
          imageio
          numpy
          resvg-py
        ]);

      in pkgs.mkShell {
        packages = [
          pythonEnv
          pkgs.resvg
          pkgs.ffmpeg
          pkgs.fira-code
          pkgs.dejavu_fonts
        ];

      };
  };
}
