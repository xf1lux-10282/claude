#!/usr/bin/env python3
"""
Precision EDN v2 - Streamlit GUI Application

プラチナプリント用デジタルネガ キャリブレーション
視覚的に操作できるWebインターフェース
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
import base64

# 既存モジュールをインポート
from data_input import MeasurementData, create_template_csv
from curve_analyzer import CurveAnalyzer
from inverse_curve import InverseCurveGenerator
from lut_export import LUTExporter
from lut_merger import LUTMerger
import config

# ===== ページ設定 =====

st.set_page_config(
    page_title="Precision EDN v2",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== カスタムCSS =====

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== ヘッダー =====

st.markdown('<div class="main-header">🎨 Precision EDN v2</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">プラチナプリント用デジタルネガ キャリブレーション</div>', unsafe_allow_html=True)

# ===== サイドバー =====

with st.sidebar:
    st.header("⚙️ 設定")

    # バージョン情報
    st.markdown(f"""
    **Version**: {config.VERSION}
    **Date**: {config.CREATED_DATE}
    **Mode**: {config.PRINT_MODE}
    """)

    st.divider()

    # 出力設定
    st.subheader("出力設定")
    output_name = st.text_input(
        "出力ファイル名",
        value="precision_edn_v2",
        help="生成されるLUTファイルの名前"
    )

    st.divider()

    # 設計パラメータ表示
    st.subheader("設計パラメータ")
    st.markdown(f"""
    - **γ**: {config.NEGATIVE_GAMMA}
    - **Dmin**: {config.NEGATIVE_DMIN}
    - **Dmax**: {config.NEGATIVE_DMAX}
    - **中間調入力**: {config.MIDTONE_INPUT}
    - **中間調濃度**: {config.MIDTONE_NEGATIVE_DENSITY}
    """)

    st.divider()

    # ヘルプ
    with st.expander("📖 ヘルプ"):
        st.markdown("""
        ### 使い方

        1. **テンプレート作成** または **CSVアップロード**
        2. 測定データを入力
        3. **LUT生成実行**
        4. 出力ファイルをダウンロード

        ### 測定手順

        - **測定①**: ネガ濃度（透過モード）
        - **測定②**: プリント濃度（反射モード）

        詳細は [USAGE.md](USAGE.md) を参照
        """)

# ===== メインエリア =====

# タブ構成
tab1, tab2, tab3, tab4 = st.tabs(["📁 データ入力", "🚀 LUT生成", "🔄 反復補正", "📚 ドキュメント"])

# ===== タブ1: データ入力 =====

with tab1:
    st.header("📁 測定データ入力")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("オプション1: テンプレート作成")

        if st.button("📝 テンプレートCSVを作成", use_container_width=True):
            # テンプレート作成
            template_path = Path(config.DATA_DIR) / "measurement_template.csv"
            create_template_csv(template_path)

            # ダウンロードボタン表示
            with open(template_path, 'r') as f:
                csv_data = f.read()

            st.download_button(
                label="💾 テンプレートをダウンロード",
                data=csv_data,
                file_name="measurement_template.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.markdown('<div class="success-box">✓ テンプレートを作成しました</div>', unsafe_allow_html=True)
            st.info("このファイルに測定データを入力してください")

    with col2:
        st.subheader("オプション2: CSVアップロード")

        uploaded_file = st.file_uploader(
            "測定データCSVをアップロード",
            type=['csv'],
            help="測定データが入力されたCSVファイル"
        )

        if uploaded_file is not None:
            st.markdown('<div class="success-box">✓ ファイルをアップロードしました</div>', unsafe_allow_html=True)

            # データをセッションステートに保存
            st.session_state['uploaded_file'] = uploaded_file

    st.divider()

    # データプレビュー
    if 'uploaded_file' in st.session_state and st.session_state['uploaded_file'] is not None:
        st.subheader("📊 データプレビュー")

        try:
            df = pd.read_csv(st.session_state['uploaded_file'])

            # データ表示
            st.dataframe(df, use_container_width=True)

            # 統計情報
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("データ数", len(df))

            with col2:
                if 'negative_density' in df.columns:
                    neg_complete = df['negative_density'].notna().sum()
                    st.metric("ネガ濃度測定", f"{neg_complete}/{len(df)}")

            with col3:
                if 'print_density' in df.columns:
                    print_complete = df['print_density'].notna().sum()
                    st.metric("プリント濃度測定", f"{print_complete}/{len(df)}")

            # データ検証
            st.subheader("✓ データ検証")

            issues = []

            # 必須列チェック
            required_cols = ['input', 'negative_density', 'print_density']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                issues.append(f"❌ 必須列が不足: {', '.join(missing_cols)}")

            # ネガ濃度チェック
            if 'negative_density' in df.columns:
                if df['negative_density'].isna().all():
                    issues.append("⚠️ ネガ濃度が未入力です")
                elif df['negative_density'].isna().any():
                    missing_count = df['negative_density'].isna().sum()
                    issues.append(f"⚠️ ネガ濃度に {missing_count} 件の欠損があります")

            # プリント濃度チェック
            if 'print_density' in df.columns:
                if df['print_density'].isna().all():
                    issues.append("⚠️ プリント濃度が未入力です（測定②が必要）")
                elif df['print_density'].isna().any():
                    missing_count = df['print_density'].isna().sum()
                    issues.append(f"⚠️ プリント濃度に {missing_count} 件の欠損があります")

            if issues:
                for issue in issues:
                    st.warning(issue)
            else:
                st.success("✓ データは正常です。LUT生成を実行できます")
                st.session_state['data_valid'] = True

        except Exception as e:
            st.error(f"❌ CSVの読み込みエラー: {e}")
            st.session_state['data_valid'] = False

# ===== タブ2: LUT生成 =====

with tab2:
    st.header("🚀 LUT生成")

    if 'uploaded_file' not in st.session_state or st.session_state['uploaded_file'] is None:
        st.markdown('<div class="info-box">📁 まず「データ入力」タブでCSVファイルをアップロードしてください</div>', unsafe_allow_html=True)

    elif not st.session_state.get('data_valid', False):
        st.markdown('<div class="warning-box">⚠️ データに問題があります。「データ入力」タブで確認してください</div>', unsafe_allow_html=True)

    else:
        st.info(f"出力名: **{output_name}**")

        if st.button("🚀 LUT生成を実行", type="primary", use_container_width=True):

            with st.spinner("解析中..."):
                try:
                    # データ読み込み
                    st.session_state['uploaded_file'].seek(0)  # ファイルポインタをリセット
                    temp_csv = Path(config.DATA_DIR) / "temp_measurement.csv"
                    with open(temp_csv, 'wb') as f:
                        f.write(st.session_state['uploaded_file'].getvalue())

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: データ読み込み
                    status_text.text("📊 データを読み込み中...")
                    progress_bar.progress(10)

                    from data_input import read_csv
                    data = read_csv(temp_csv)

                    # Step 2: カーブ解析
                    status_text.text("📈 カーブを解析中...")
                    progress_bar.progress(30)

                    analyzer = CurveAnalyzer(data)
                    analyzer.analyze_negative_curve()
                    analyzer.analyze_print_curve()
                    analyzer.analyze_combined_curve()

                    # Step 3: 逆カーブ生成
                    status_text.text("🔄 逆カーブを生成中...")
                    progress_bar.progress(50)

                    inverse_gen = InverseCurveGenerator(analyzer)
                    inverse_gen.generate_inverse_curve()

                    # Step 4: LUTエクスポート
                    status_text.text("💾 LUTをエクスポート中...")
                    progress_bar.progress(70)

                    exporter = LUTExporter(inverse_gen)
                    exporter.export_all(config.LUTS_DIR, output_name)

                    # グラフ生成
                    status_text.text("📊 基本グラフを生成中...")
                    progress_bar.progress(70)

                    graph_path = analyzer.generate_graphs(config.GRAPHS_DIR)

                    # プレビューグラフ生成
                    status_text.text("🔍 プレビューグラフを生成中...")
                    progress_bar.progress(75)

                    from curve_analyzer import (
                        generate_preview_graph,
                        generate_histogram_graph,
                        generate_error_graph,
                        generate_lut_curve_graph,
                        generate_gamma_graph,
                        generate_interactive_graphs
                    )
                    preview_path = generate_preview_graph(analyzer, inverse_gen, config.GRAPHS_DIR)

                    # 追加グラフ生成
                    status_text.text("📊 ヒストグラムを生成中...")
                    progress_bar.progress(80)
                    histogram_path = generate_histogram_graph(analyzer, config.GRAPHS_DIR)

                    status_text.text("📊 誤差グラフを生成中...")
                    progress_bar.progress(85)
                    error_path = generate_error_graph(analyzer, inverse_gen, config.GRAPHS_DIR)

                    status_text.text("📊 LUTカーブを生成中...")
                    progress_bar.progress(90)
                    lut_curve_path = generate_lut_curve_graph(inverse_gen, config.GRAPHS_DIR)

                    status_text.text("📊 ガンマ特性グラフを生成中...")
                    progress_bar.progress(93)
                    gamma_path = generate_gamma_graph(analyzer, config.GRAPHS_DIR)

                    status_text.text("🎨 インタラクティブグラフを生成中...")
                    progress_bar.progress(96)
                    interactive_paths = generate_interactive_graphs(analyzer, inverse_gen, config.GRAPHS_DIR)

                    progress_bar.progress(100)
                    status_text.text("✓ 完了！")

                    # 成功メッセージ
                    st.markdown('<div class="success-box">✓ LUT生成が完了しました！</div>', unsafe_allow_html=True)

                    # 結果を保存
                    st.session_state['lut_generated'] = True
                    st.session_state['output_name'] = output_name
                    st.session_state['graph_path'] = graph_path
                    st.session_state['preview_path'] = preview_path
                    st.session_state['histogram_path'] = histogram_path
                    st.session_state['error_path'] = error_path
                    st.session_state['lut_curve_path'] = lut_curve_path
                    st.session_state['gamma_path'] = gamma_path
                    st.session_state['interactive_paths'] = interactive_paths
                    st.session_state['exporter'] = exporter
                    st.session_state['analyzer'] = analyzer
                    st.session_state['inverse_gen'] = inverse_gen

                    # 一時ファイル削除
                    temp_csv.unlink()

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # 結果表示
        if st.session_state.get('lut_generated', False):
            st.divider()

            st.subheader("📊 解析結果")

            # タブで各種グラフを表示
            graph_tabs = st.tabs([
                "📈 基本カーブ",
                "📊 ヒストグラム",
                "📉 誤差解析",
                "🎯 LUTカーブ",
                "📐 ガンマ特性",
                "🔍 LUT適用予測",
                "🎨 インタラクティブ"
            ])

            # タブ1: 基本カーブ
            with graph_tabs[0]:
                if 'graph_path' in st.session_state:
                    st.image(st.session_state['graph_path'], use_container_width=True)
                    st.caption("プリンター特性、プラチナプリント特性、合成特性の3つのカーブ")

            # タブ2: ヒストグラム
            with graph_tabs[1]:
                if 'histogram_path' in st.session_state:
                    st.image(st.session_state['histogram_path'], use_container_width=True)
                    st.caption("測定値の分布（ネガ濃度とプリント濃度）")

            # タブ3: 誤差解析
            with graph_tabs[2]:
                if 'error_path' in st.session_state:
                    st.image(st.session_state['error_path'], use_container_width=True)
                    st.caption("理想線形カーブからの誤差（LUT適用前後の比較）")

            # タブ4: LUTカーブ
            with graph_tabs[3]:
                if 'lut_curve_path' in st.session_state:
                    st.image(st.session_state['lut_curve_path'], use_container_width=True)
                    st.caption("生成されたLUTカーブと制御点")

            # タブ5: ガンマ特性
            with graph_tabs[4]:
                if 'gamma_path' in st.session_state:
                    st.image(st.session_state['gamma_path'], use_container_width=True)
                    st.caption(f"ネガのガンマ応答（設計値: γ={config.NEGATIVE_GAMMA}）")

            # タブ6: LUT適用予測
            with graph_tabs[5]:
                if 'preview_path' in st.session_state:
                    st.image(st.session_state['preview_path'], use_container_width=True)
                    st.caption("LUT適用前後の特性比較（予測）")

            # タブ7: インタラクティブグラフ
            with graph_tabs[6]:
                if 'interactive_paths' in st.session_state:
                    st.subheader("🎨 インタラクティブグラフ")

                    st.markdown("以下のリンクからインタラクティブグラフをダウンロードして、ブラウザで開いてください。")
                    st.markdown("グラフ上にマウスを置くと詳細な値が表示され、ズームやパンも可能です。")

                    col1, col2 = st.columns(2)

                    with col1:
                        if 'curves' in st.session_state['interactive_paths']:
                            with open(st.session_state['interactive_paths']['curves'], 'r', encoding='utf-8') as f:
                                html_data = f.read()

                            st.download_button(
                                label="📥 インタラクティブ解析グラフ (HTML)",
                                data=html_data,
                                file_name=f"{st.session_state['output_name']}_interactive_curves.html",
                                mime="text/html",
                                use_container_width=True
                            )

                    with col2:
                        if 'lut' in st.session_state['interactive_paths']:
                            with open(st.session_state['interactive_paths']['lut'], 'r', encoding='utf-8') as f:
                                html_data = f.read()

                            st.download_button(
                                label="📥 インタラクティブLUTグラフ (HTML)",
                                data=html_data,
                                file_name=f"{st.session_state['output_name']}_interactive_lut.html",
                                mime="text/html",
                                use_container_width=True
                            )

                    # HTMLを直接表示（オプション）
                    st.markdown("---")
                    st.markdown("**プレビュー: インタラクティブ解析グラフ**")

                    if 'curves' in st.session_state['interactive_paths']:
                        with open(st.session_state['interactive_paths']['curves'], 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=600, scrolling=True)

            st.divider()

            st.subheader("💾 ダウンロード")

            col1, col2, col3 = st.columns(3)

            with col1:
                # CUBE LUTダウンロード
                cube_path = Path(config.LUTS_DIR) / f"{st.session_state['output_name']}.cube"
                if cube_path.exists():
                    with open(cube_path, 'r') as f:
                        cube_data = f.read()

                    st.download_button(
                        label="📥 CUBE LUT",
                        data=cube_data,
                        file_name=f"{st.session_state['output_name']}.cube",
                        mime="text/plain",
                        use_container_width=True
                    )

            with col2:
                # カーブCSVダウンロード
                csv_path = Path(config.LUTS_DIR) / f"{st.session_state['output_name']}_curve.csv"
                if csv_path.exists():
                    with open(csv_path, 'r') as f:
                        csv_data = f.read()

                    st.download_button(
                        label="📥 カーブCSV",
                        data=csv_data,
                        file_name=f"{st.session_state['output_name']}_curve.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            with col3:
                # レポートダウンロード
                report_path = Path(config.LUTS_DIR) / f"{st.session_state['output_name']}_report.txt"
                if report_path.exists():
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_data = f.read()

                    st.download_button(
                        label="📥 レポート",
                        data=report_data,
                        file_name=f"{st.session_state['output_name']}_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

            # グラフPDFダウンロード
            col4, col5 = st.columns(2)

            with col4:
                graph_path = Path(config.GRAPHS_DIR) / "analysis_curves.pdf"
                if graph_path.exists():
                    with open(graph_path, 'rb') as f:
                        pdf_data = f.read()

                    st.download_button(
                        label="📥 解析グラフ (PDF)",
                        data=pdf_data,
                        file_name=f"{st.session_state['output_name']}_analysis.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            with col5:
                # プレビューグラフPDFダウンロード
                if 'preview_path' in st.session_state:
                    preview_path = Path(st.session_state['preview_path'])
                    if preview_path.exists():
                        with open(preview_path, 'rb') as f:
                            preview_pdf_data = f.read()

                        st.download_button(
                            label="🔍 LUT適用プレビュー (PDF)",
                            data=preview_pdf_data,
                            file_name=f"{st.session_state['output_name']}_preview.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

# ===== タブ3: 反復補正 =====

with tab3:
    st.header("🔄 反復補正モード")

    st.markdown("""
    LUT適用後に再測定したデータから、さらに精度を高めるための補正LUTを生成・統合します。

    ### ワークフロー
    1. 初回生成したLUTでチャートを印刷
    2. 再度濃度測定（ネガ + プリント）
    3. このタブで既存LUTと再測定データをアップロード
    4. 補正LUTを自動生成・マージ
    5. より高精度なLUTを取得
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1️⃣ 既存LUTをアップロード")

        base_lut_file = st.file_uploader(
            "既存のCUBE LUTファイル",
            type=['cube'],
            help="初回生成したLUTファイル",
            key="base_lut_uploader"
        )

        if base_lut_file is not None:
            st.markdown('<div class="success-box">✓ ベースLUTをアップロードしました</div>', unsafe_allow_html=True)
            st.session_state['base_lut_uploaded'] = True
            st.session_state['base_lut_file'] = base_lut_file

    with col2:
        st.subheader("2️⃣ 再測定データをアップロード")

        remeasure_csv_file = st.file_uploader(
            "再測定データCSV（2回目）",
            type=['csv'],
            help="LUT適用後のチャートを再測定したCSV",
            key="remeasure_csv_uploader"
        )

        if remeasure_csv_file is not None:
            st.markdown('<div class="success-box">✓ 再測定データをアップロードしました</div>', unsafe_allow_html=True)
            st.session_state['remeasure_csv_uploaded'] = True
            st.session_state['remeasure_csv_file'] = remeasure_csv_file

    st.divider()

    # データプレビュー
    if st.session_state.get('remeasure_csv_uploaded', False):
        st.subheader("📊 再測定データプレビュー")

        try:
            df_remeasure = pd.read_csv(st.session_state['remeasure_csv_file'])
            st.dataframe(df_remeasure, use_container_width=True)

            # 統計情報
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("データ数", len(df_remeasure))

            with col2:
                if 'negative_density' in df_remeasure.columns:
                    neg_complete = df_remeasure['negative_density'].notna().sum()
                    st.metric("ネガ濃度測定", f"{neg_complete}/{len(df_remeasure)}")

            with col3:
                if 'print_density' in df_remeasure.columns:
                    print_complete = df_remeasure['print_density'].notna().sum()
                    st.metric("プリント濃度測定", f"{print_complete}/{len(df_remeasure)}")

        except Exception as e:
            st.error(f"❌ CSVの読み込みエラー: {e}")

    st.divider()

    # 反復補正実行
    if st.session_state.get('base_lut_uploaded', False) and st.session_state.get('remeasure_csv_uploaded', False):

        st.subheader("3️⃣ 補正LUT生成・マージ")

        merge_output_name = st.text_input(
            "マージ後のLUT名",
            value=f"{output_name}_iteration2",
            help="生成される統合LUTの名前"
        )

        if st.button("🔄 補正LUT生成・マージを実行", type="primary", use_container_width=True):

            with st.spinner("補正LUT生成中..."):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: ベースLUTを読み込む
                    status_text.text("📂 ベースLUTを読み込み中...")
                    progress_bar.progress(10)

                    # 一時ファイルに保存
                    base_lut_path = Path(config.DATA_DIR) / "temp_base_lut.cube"
                    with open(base_lut_path, 'wb') as f:
                        st.session_state['base_lut_file'].seek(0)
                        f.write(st.session_state['base_lut_file'].getvalue())

                    merger = LUTMerger()
                    base_lut_array = merger.read_cube_lut(str(base_lut_path))

                    # Step 2: 再測定データを読み込む
                    status_text.text("📊 再測定データを読み込み中...")
                    progress_bar.progress(20)

                    remeasure_csv_path = Path(config.DATA_DIR) / "temp_remeasure.csv"
                    with open(remeasure_csv_path, 'wb') as f:
                        st.session_state['remeasure_csv_file'].seek(0)
                        f.write(st.session_state['remeasure_csv_file'].getvalue())

                    from data_input import read_csv
                    remeasure_data = read_csv(remeasure_csv_path)

                    # Step 3: 再測定データから補正LUTを生成
                    status_text.text("🔄 補正LUTを生成中...")
                    progress_bar.progress(40)

                    analyzer_remeasure = CurveAnalyzer(remeasure_data)
                    analyzer_remeasure.analyze_negative_curve()
                    analyzer_remeasure.analyze_print_curve()
                    analyzer_remeasure.analyze_combined_curve()

                    inverse_gen_correction = InverseCurveGenerator(analyzer_remeasure)
                    inverse_gen_correction.generate_inverse_curve()

                    correction_lut_array = inverse_gen_correction.get_curve_as_lut(resolution=256)

                    # Step 4: 補正LUTをCUBE形式で一時保存
                    status_text.text("💾 補正LUTを保存中...")
                    progress_bar.progress(60)

                    correction_lut_path = Path(config.LUTS_DIR) / "temp_correction_lut.cube"
                    merger.save_cube_lut(correction_lut_array, str(correction_lut_path), "Correction LUT")

                    # Step 5: LUTをマージ
                    status_text.text("🔀 LUTをマージ中...")
                    progress_bar.progress(80)

                    merged_lut_array = merger.merge_luts(base_lut_array, correction_lut_array)

                    # Step 6: マージ後のLUTを保存
                    status_text.text("💾 マージ後のLUTを保存中...")
                    progress_bar.progress(90)

                    merged_lut_path = Path(config.LUTS_DIR) / f"{merge_output_name}.cube"
                    merger.save_cube_lut(
                        merged_lut_array,
                        str(merged_lut_path),
                        f"Precision EDN v2 - Merged LUT (Iteration 2)"
                    )

                    # プレビューグラフ生成
                    status_text.text("🔍 プレビューグラフを生成中...")
                    progress_bar.progress(95)

                    from curve_analyzer import generate_preview_graph
                    preview_path_merged = generate_preview_graph(
                        analyzer_remeasure,
                        inverse_gen_correction,
                        config.GRAPHS_DIR
                    )

                    progress_bar.progress(100)
                    status_text.text("✓ 完了！")

                    # 成功メッセージ
                    st.markdown('<div class="success-box">✓ 補正LUT生成・マージが完了しました！</div>', unsafe_allow_html=True)

                    # 結果を保存
                    st.session_state['merged_lut_generated'] = True
                    st.session_state['merged_lut_name'] = merge_output_name
                    st.session_state['merged_lut_path'] = merged_lut_path
                    st.session_state['correction_lut_path'] = correction_lut_path
                    st.session_state['preview_path_merged'] = preview_path_merged

                    # 一時ファイル削除
                    base_lut_path.unlink()
                    remeasure_csv_path.unlink()

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # 結果表示
        if st.session_state.get('merged_lut_generated', False):
            st.divider()

            st.subheader("📊 マージ結果")

            st.success(f"✓ マージ後のLUT: **{st.session_state['merged_lut_name']}.cube**")

            st.divider()

            st.subheader("💾 ダウンロード")

            col1, col2, col3 = st.columns(3)

            with col1:
                # マージ後のCUBE LUTダウンロード
                if st.session_state['merged_lut_path'].exists():
                    with open(st.session_state['merged_lut_path'], 'r') as f:
                        merged_cube_data = f.read()

                    st.download_button(
                        label="📥 マージ後 CUBE LUT",
                        data=merged_cube_data,
                        file_name=f"{st.session_state['merged_lut_name']}.cube",
                        mime="text/plain",
                        use_container_width=True
                    )

            with col2:
                # 補正LUTダウンロード（参考用）
                if st.session_state['correction_lut_path'].exists():
                    with open(st.session_state['correction_lut_path'], 'r') as f:
                        correction_cube_data = f.read()

                    st.download_button(
                        label="📥 補正LUT (参考)",
                        data=correction_cube_data,
                        file_name=f"{st.session_state['merged_lut_name']}_correction.cube",
                        mime="text/plain",
                        use_container_width=True
                    )

            with col3:
                # プレビューPDFダウンロード
                if 'preview_path_merged' in st.session_state:
                    preview_path = Path(st.session_state['preview_path_merged'])
                    if preview_path.exists():
                        with open(preview_path, 'rb') as f:
                            preview_pdf_data = f.read()

                        st.download_button(
                            label="🔍 プレビュー (PDF)",
                            data=preview_pdf_data,
                            file_name=f"{st.session_state['merged_lut_name']}_preview.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

    else:
        st.markdown('<div class="info-box">📁 ベースLUTと再測定データの両方をアップロードしてください</div>', unsafe_allow_html=True)

# ===== タブ4: ドキュメント =====

with tab4:
    st.header("📚 ドキュメント")

    doc_tabs = st.tabs(["使い方", "ワークフロー", "設計パラメータ"])

    with doc_tabs[0]:
        st.subheader("📖 Precision EDN v2 使い方")

        st.markdown("""
        ### 基本的な流れ

        1. **測定用チャート作成**
           - Photoshopスクリプトで33ステップチャート生成
           - RGB変換 → 反転 → Color Blocker → 印刷

        2. **測定①: ネガ濃度測定**
           - 濃度計（透過モード）で33ステップ測定
           - テンプレートCSVに入力

        3. **測定②: プリント濃度測定**
           - 同じネガでプラチナプリント作成
           - 濃度計（反射モード）で測定
           - 同じCSVに追記

        4. **LUT生成**
           - このアプリでCSVをアップロード
           - LUT生成実行
           - CUBE LUTをダウンロード

        5. **本番作品制作**
           - Photoshopで CUBE LUT を適用
           - 反転 → Color Blocker → 印刷

        ### 詳細ドキュメント

        - [USAGE.md](USAGE.md) - 詳細な使用方法
        - [WORKFLOW_RGB_ColorBlocker.md](WORKFLOW_RGB_ColorBlocker.md) - 完全ワークフロー
        - [README.md](README.md) - プロジェクト概要
        """)

    with doc_tabs[1]:
        st.subheader("🔄 RGB + Color Blocker ワークフロー")

        st.markdown("""
        ### 測定フェーズ

        ```
        33ステップチャート（RGB）
          ↓
        階調の反転
          ↓
        Color Blocker適用
          ↓
        カラーモード印刷（クリスピア、レベル4、5760dpi）
          ↓
        ネガ濃度測定① → CSV
          ↓
        プラチナプリント作成
          ↓
        プリント濃度測定② → CSV
          ↓
        Precision EDN v2 実行
          ↓
        LUT生成
        ```

        ### 本番フェーズ

        ```
        RAW現像画像（16bit RGB）
          ↓
        Lightroom/Photoshop 基本編集
          ↓
        Precision EDN v2 LUT適用
          ↓
        階調の反転
          ↓
        Color Blocker適用
          ↓
        カラーモード印刷
          ↓
        ネガ完成
          ↓
        プラチナプリント完成
        ```
        """)

    with doc_tabs[2]:
        st.subheader("⚙️ Version 2 設計パラメータ")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### ネガ設計値

            - **γ**: 1.8
            - **Dmin**: 0.10
            - **Dmax**: 2.10 (カラーモード)
            - **濃度レンジ**: 2.0

            ### 中間調基準点

            - **入力値**: 128
            - **ネガ濃度**: 0.70
            """)

        with col2:
            st.markdown("""
            ### プリント目標値

            - **Dmax**: 2.1以上
            - **露光レンジ**: 約6.6 EV

            ### プリンター設定

            - **機種**: EPSON PX-1V
            - **用紙設定**: クリスピア
            - **モード**: カラー
            - **解像度**: 5760x1440dpi
            - **品質**: レベル4
            """)

# ===== フッター =====

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**Version**: {config.VERSION}")

with col2:
    st.markdown(f"**Created**: {config.CREATED_DATE}")

with col3:
    st.markdown(f"**Mode**: {config.WORKFLOW_TYPE}")
