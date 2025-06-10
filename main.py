import json
import requests
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Browser


class FinancialAgent:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _extract_table_data(self, table_selector: str) -> pd.DataFrame:
        self.page.wait_for_selector(table_selector)
        table_element = self.page.locator(table_selector)

        headers = [th.text_content().strip() for th in table_element.locator("thead th").all()]

        data = []
        for row in table_element.locator("tbody tr").all():
            row_data = []
            for td in row.locator("td").all():
                if td.locator("a").count() > 0:
                    row_data.append(td.locator("a").text_content().strip())
                else:
                    row_data.append(td.text_content().strip())
            data.append(row_data)

        return pd.DataFrame(data, columns=headers)

    def extrair_altas_e_baixas(self, url: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        self.page.goto(url)

        df_altas = self._extract_table_data("#high_wrapper table")

        self.page.get_by_role("button", name="Baixas").click()
        df_baixas = self._extract_table_data("#low_wrapper table")

        return df_altas, df_baixas


if __name__ == "__main__":
    infomoney_ibovespa_url = "https://www.infomoney.com.br/cotacoes/b3/indice/ibovespa/"
    with FinancialAgent(headless=True) as agent:
        df_altas, df_baixas = agent.extrair_altas_e_baixas(infomoney_ibovespa_url)
        df_all = pd.concat([df_baixas, df_altas], ignore_index=True)

    print(df_altas, df_baixas, df_all)
