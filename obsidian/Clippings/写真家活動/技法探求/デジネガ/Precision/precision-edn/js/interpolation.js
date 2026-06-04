/**
 * Precision EDN - 補間アルゴリズム
 * PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)
 * トーンジャンプを防ぐ単調性保持補間
 */

class Interpolation {
  /**
   * PCHIP補間
   * @param {Array} x - 入力値配列（昇順）
   * @param {Array} y - 出力値配列
   * @param {number} points - 補間後のポイント数
   * @returns {Array} 補間された値の配列
   */
  static pchip(x, y, points = 1024) {
    if (x.length !== y.length) {
      throw new Error('x と y の長さが一致しません');
    }

    const n = x.length;
    if (n < 2) {
      throw new Error('最低2ポイント必要です');
    }

    // 各区間の傾きを計算
    const delta = [];
    for (let i = 0; i < n - 1; i++) {
      delta[i] = (y[i + 1] - y[i]) / (x[i + 1] - x[i]);
    }

    // 各点での微分値を計算（単調性を保持）
    const m = new Array(n);
    m[0] = delta[0];
    m[n - 1] = delta[n - 2];

    for (let i = 1; i < n - 1; i++) {
      if (delta[i - 1] * delta[i] <= 0) {
        // 符号が変わる場合（極値）は0
        m[i] = 0;
      } else {
        // 調和平均を使用（単調性保持）
        const w1 = 2 * (x[i + 1] - x[i]) + (x[i] - x[i - 1]);
        const w2 = (x[i + 1] - x[i]) + 2 * (x[i] - x[i - 1]);
        m[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i]);
      }
    }

    // 補間値を生成
    const result = [];
    const xMin = x[0];
    const xMax = x[n - 1];
    const step = (xMax - xMin) / (points - 1);

    for (let i = 0; i < points; i++) {
      const xi = xMin + i * step;

      // xiが属する区間を見つける
      let k = 0;
      for (let j = 0; j < n - 1; j++) {
        if (xi >= x[j] && xi <= x[j + 1]) {
          k = j;
          break;
        }
      }

      // エルミート補間
      const h = x[k + 1] - x[k];
      const t = (xi - x[k]) / h;
      const t2 = t * t;
      const t3 = t2 * t;

      const h00 = 2 * t3 - 3 * t2 + 1;
      const h10 = t3 - 2 * t2 + t;
      const h01 = -2 * t3 + 3 * t2;
      const h11 = t3 - t2;

      const yi = h00 * y[k] + h10 * h * m[k] + h01 * y[k + 1] + h11 * h * m[k + 1];

      result.push(yi);
    }

    return result;
  }

  /**
   * Catmull-Rom スプライン補間（より滑らか）
   * @param {Array} x - 入力値配列
   * @param {Array} y - 出力値配列
   * @param {number} points - 補間後のポイント数
   * @returns {Array} 補間された値の配列
   */
  static catmullRom(x, y, points = 1024) {
    const n = x.length;
    if (n < 2) {
      throw new Error('最低2ポイント必要です');
    }

    const result = [];
    const xMin = x[0];
    const xMax = x[n - 1];
    const step = (xMax - xMin) / (points - 1);

    for (let i = 0; i < points; i++) {
      const xi = xMin + i * step;

      // 区間を見つける
      let k = 0;
      for (let j = 0; j < n - 1; j++) {
        if (xi >= x[j] && xi <= x[j + 1]) {
          k = j;
          break;
        }
      }

      // Catmull-Romのための4点を取得
      const p0 = k > 0 ? y[k - 1] : y[k];
      const p1 = y[k];
      const p2 = y[k + 1];
      const p3 = k < n - 2 ? y[k + 2] : y[k + 1];

      const t = (xi - x[k]) / (x[k + 1] - x[k]);
      const t2 = t * t;
      const t3 = t2 * t;

      const yi = 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
      );

      result.push(yi);
    }

    return result;
  }

  /**
   * 線形補間（シンプル、高速）
   * @param {Array} x - 入力値配列
   * @param {Array} y - 出力値配列
   * @param {number} points - 補間後のポイント数
   * @returns {Array} 補間された値の配列
   */
  static linear(x, y, points = 1024) {
    const n = x.length;
    if (n < 2) {
      throw new Error('最低2ポイント必要です');
    }

    const result = [];
    const xMin = x[0];
    const xMax = x[n - 1];
    const step = (xMax - xMin) / (points - 1);

    for (let i = 0; i < points; i++) {
      const xi = xMin + i * step;

      // 区間を見つける
      let k = 0;
      for (let j = 0; j < n - 1; j++) {
        if (xi >= x[j] && xi <= x[j + 1]) {
          k = j;
          break;
        }
      }

      // 線形補間
      const t = (xi - x[k]) / (x[k + 1] - x[k]);
      const yi = y[k] + t * (y[k + 1] - y[k]);

      result.push(yi);
    }

    return result;
  }

  /**
   * 補間方法を名前で選択
   * @param {string} method - "pchip", "catmullrom", "linear"
   * @param {Array} x - 入力値配列
   * @param {Array} y - 出力値配列
   * @param {number} points - 補間後のポイント数
   * @returns {Array} 補間された値の配列
   */
  static interpolate(method, x, y, points = 1024) {
    switch(method.toLowerCase()) {
      case 'pchip':
        return this.pchip(x, y, points);
      case 'catmullrom':
      case 'catmull-rom':
        return this.catmullRom(x, y, points);
      case 'linear':
        return this.linear(x, y, points);
      default:
        console.warn(`未知の補間方法: ${method}、PCHIPを使用します`);
        return this.pchip(x, y, points);
    }
  }
}
