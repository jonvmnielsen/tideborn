#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornSaveComponent.generated.h"

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornSaveComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornSaveComponent();

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Save")
	FString SlotName = TEXT("TidebornCamp");

	UFUNCTION(BlueprintCallable, Category="Tideborn|Save")
	bool SaveCamp();

	UFUNCTION(BlueprintCallable, Category="Tideborn|Save")
	bool LoadCamp();

private:
	void BindHotkeys();
	void OnSaveKey();
	void OnLoadKey();
};
