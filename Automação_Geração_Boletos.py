import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time


driver_path = 'C:/Users/Bruno/Desktop/chromedriver-win64/chromedriver.exe'
service = Service(driver_path)


df = pd.read_excel('recibos.xlsx')


for index, row in df.iterrows():
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    driver.get('https://www.cobrefacil.com.br/recibo-online')

    wait = WebDriverWait(driver, 20)

 
    try:
        aceitar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/div/button[1]'))
        )
        aceitar.click()
        print("✅ Botão de cookies 'Aceitar' clicado.")
    except:
        print("⚠️ Botão de cookies não apareceu ou já estava fechado.")

   
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(2)

 
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="receiptgeneratorform-receiptdate"]')))
    data_formatada = pd.to_datetime(row['data']).strftime('%d/%m/%Y')
    driver.find_element(By.ID, 'receiptgeneratorform-receiptdate').send_keys(data_formatada)


  
    driver.find_element(By.ID, 'receiptgeneratorform-receiptnumber').send_keys(str(row['numero']))
    driver.find_element(By.ID, 'receiptgeneratorform-payername').send_keys(str(row['pagador']))
    driver.find_element(By.ID, 'receiptgeneratorform-payercpfcnpj').send_keys(str(row['doc_pagador']))
    driver.find_element(By.ID, 'receiptgeneratorform-payerphone').send_keys(str(row['tel_pagador']))
    driver.find_element(By.ID, 'receiptgeneratorform-payeename').send_keys(str(row['beneficiario']))
    driver.find_element(By.ID, 'receiptgeneratorform-payeecpfcnpj').send_keys(str(row['doc_beneficiario']))

  
    driver.find_element(By.XPATH, '//span[@id="select2-receiptgeneratorform-payeestate-container"]').click()
    wait.until(EC.presence_of_element_located((By.XPATH, '//li[contains(text(), "Alagoas")]'))).click()
    time.sleep(1)


    driver.find_element(By.XPATH, '//span[@id="select2-receiptgeneratorform-payeecity-container"]').click()
    wait.until(EC.presence_of_element_located((By.XPATH, '//li[contains(text(), "Maceió")]'))).click()

  
    driver.find_element(By.ID, 'receiptgeneratorform-servicedescription-0').send_keys(str(row['descricao']))
    driver.find_element(By.ID, 'receiptgeneratorform-servicequantity-0').send_keys(str(row['qtd']))
    driver.find_element(By.ID, 'receiptgeneratorform-servicetotal-0').send_keys(str(row['valor']))

   
    driver.find_element(By.ID, 'receiptgeneratorform-description').send_keys('Conforme contrato firmado')
    driver.find_element(By.ID, 'receiptgeneratorform-email').send_keys(str(row['email']))


    driver.find_element(By.ID, 'receiptgeneratorform-terms').click()

    # Botão de envio - clica via JavaScript para evitar bloqueio
    botao_xpath = '//*[@id="form-receipt"]/div[7]/div[3]/button'
    botao_envio = wait.until(EC.element_to_be_clickable((By.XPATH, botao_xpath)))
    driver.execute_script("arguments[0].scrollIntoView();", botao_envio)
    driver.execute_script("arguments[0].click();", botao_envio)

    print(f'✅ Recibo gerado para {row["pagador"]}')
    time.sleep(10)
    driver.quit()

print("✅ Todos os recibos foram gerados com sucesso!")
