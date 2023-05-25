// modified from https://github.com/07akioni/xicons/issues/364#issuecomment-1118129894

import { readdirSync } from 'fs';
import { resolveModule } from 'local-pkg';
import { dirname } from 'path';
import type { ComponentResolver } from 'unplugin-vue-components/types';

let _cache: Map<string, string>;

export interface IconResolverOptions {
  pkgs: string[],
  prefix?: string
}

export function IconComponentResolver(options: IconResolverOptions): ComponentResolver {
  if (!_cache) {
    _cache = new Map<string, string>();
    for (const pkg of options.pkgs) {
      try {
        const icon_path = resolveModule(pkg) as string;
        const icons = readdirSync(dirname(icon_path), { withFileTypes: true })
          .filter(item => !item.isDirectory() && item.name.match(/^[A-Z][A-Za-z0-9]+\.js$/))
          .map(item => item.name.replace(/\.js$/, ''));

        for (const icon of icons) {
          if (!_cache.has(icon)) {
            _cache.set(icon, pkg);
          }
        }

        console.log(`[unplugin-vue-components] loaded ${icons.length} icons from "${pkg}"`);
      } catch (error) {
        console.error(error);
        throw new Error(`[unplugin-vue-components] failed to load "${pkg}", have you installed it?`);
      }
    }
  }

  return {
    type: 'component',
    resolve: (name: string) => {
      if (options.prefix && name.startsWith(options.prefix)) {
        name = name.substring(options.prefix.length);
      }

      if (_cache.has(name)) {
        return {
          name: name,
          from: _cache.get(name),
        };
      }
    },
  };
}
