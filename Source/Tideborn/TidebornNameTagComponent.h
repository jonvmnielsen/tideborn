#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornNameTagComponent.generated.h"

class UTextRenderComponent;

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornNameTagComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornNameTagComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|UI")
	FString Title;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|UI")
	FString Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|UI")
	float HeightOffset = 140.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|UI")
	float TitleSize = 48.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|UI")
	FColor TitleColor = FColor::Yellow;

	void SetLabel(const FString& InTitle, const FString& InSubtitle);

private:
	UPROPERTY()
	TObjectPtr<UTextRenderComponent> TitleText;

	UPROPERTY()
	TObjectPtr<UTextRenderComponent> SubtitleText;
};
